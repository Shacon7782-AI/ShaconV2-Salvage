import os
import json
import uuid
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy.orm import Session
from app.db.schemas.session import SessionLocal
from app.db.schemas.models import SovereignMemoryNode

import faiss
import gc
from contextlib import contextmanager
from app.core.immudb_sidecar import immudb

# Optimization: Limit FAISS to 4 cores to leave room for visual dev/Ollama
os.environ["OMP_NUM_THREADS"] = "4"

# Sovereign Tuning: IPEX/SYCL for Intel iGPU Offloading
# Ensures persistent caching and minimizes Level Zero latency
os.environ["SYCL_CACHE_PERSISTENT"] = "1"
os.environ["SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS"] = "1"
os.environ["USE_XETLA"] = "OFF" # Critical for Iris Xe stability

class SovereignMemory:
    """
    Persistent Vector Memory for Shacon v2.0 -> v5.0
    Hybrid Backend: 
    1. Local Buffer (FAISS + JSON) - Always available, Docker-independent.
    2. Primary Store (Postgres pgvector) - Source of truth for long-term scale.
    """
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2", 
                 storage_dir: Optional[str] = None):
        self.model_name = model_name
        self.encoder_model = None
        self.reranker_model = None
        
        # Hardware Detection: Check for Intel XPU (IPEX)
        self.device = "cpu"
        try:
            import torch
            if hasattr(torch, "xpu") and torch.xpu.is_available():
                import intel_extension_for_pytorch as ipex
                self.device = "xpu"
                print(f"[MEMORY] DISCOVERED INTEL XPU: Offloading to Iris Xe iGPU.")
        except ImportError:
            # Check for standard CUDA or fallback to CPU
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
            except: pass
        
        # 1. Initialize dimensions 
        print(f"[MEMORY] Initializing Sovereign Recall (Model: {model_name})")
        
        # We know MiniLM-L6 is 384. For others, we might need to load.
        if "MiniLM-L6" in model_name:
            self.dimension = 384
        else:
            # Temporary load to get dimension (wrapped to avoid crashes in some envs)
            try:
                temp_model = SentenceTransformer(model_name)
                self.dimension = temp_model.get_sentence_embedding_dimension()
                del temp_model
                gc.collect()
            except Exception as e:
                print(f"[MEMORY] Warning: Could not auto-detect dimension, using default 384. Error: {e}")
                self.dimension = 384

        # 2. Initialize Local FAISS Buffer
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.buffer_path = os.path.join(base_dir, "local_memory_buffer_faiss")
        os.makedirs(self.buffer_path, exist_ok=True)
        
        self.index_file = os.path.join(self.buffer_path, "index.faiss")
        self.metadata_file = os.path.join(self.buffer_path, "metadata.json")
        
        # Load or create index
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.metadata_file, "r") as f:
                self.buffer_metadata = json.load(f)
        else:
            # OPTIMIZATION: Use Scalar Quantizer (QT_8bit) to reduce vector RAM usage by 75%
            # IndexFlatL2 uses 4 bytes/dim. IndexScalarQuantizer with QT_8bit uses 1 byte/dim.
            self.index = faiss.IndexScalarQuantizer(self.dimension, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_L2)
            self.buffer_metadata = [] # List of {id, content, metadata}
            
        print(f"[MEMORY] Local FAISS (Quantized) Buffer initialized at {self.buffer_path} ({len(self.buffer_metadata)} entries)")

    def _persist_buffer(self):
        """Saves FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, "w") as f:
            json.dump(self.buffer_metadata, f, indent=2)
        gc.collect()

    @contextmanager
    def _get_models(self):
        """Lazy-loading context manager to keep RAM usage low."""
        try:
            if not self.encoder_model:
                print(f"[MEMORY] Hot-loading Encoder ({self.model_name})...")
                self.encoder_model = SentenceTransformer(self.model_name)
            if not self.reranker_model:
                print("[MEMORY] Hot-loading Reranker...")
                self.reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            yield self.encoder_model, self.reranker_model
        finally:
            # Purge models from RAM immediately after use
            # Note: In high-frequency chat, we might want a timeout cache, 
            # but for visual dev, instant purging is safer.
            del self.encoder_model
            del self.reranker_model
            self.encoder_model = None
            self.reranker_model = None
            gc.collect()

    def commit_to_memory(self, content: str, metadata: Dict[str, Any]):
        """
        Dual-Commit strategy:
        1. Always writes to Local FAISS (Guaranteed persistence).
        2. Attempts to write to Postgres (pgvector).
        """
        chunks = self._chunk_content(content)
        timestamp = datetime.utcnow().isoformat()
        
        with self._get_models() as (encoder, _):
            # Move compute to detected hardware (XPU/CUDA/CPU)
            embeddings = encoder.encode(chunks, device=self.device).astype('float32')

        # A. Commit to Local FAISS (The Failsafe)
        try:
            self.index.add(embeddings)
            for i, chunk in enumerate(chunks):
                self.buffer_metadata.append({
                    "id": str(uuid.uuid4()),
                    "content": chunk,
                    "metadata": {**metadata, "timestamp": timestamp},
                    "synced": False
                })
            self._persist_buffer()
            print(f"[MEMORY] Local Buffer SUCCESS: {len(chunks)} chunks recorded.")
            
            # Audit the operation with Immudb Sidecar
            immudb.log_operation(
                "MEMORY_COMMIT", 
                {"chunks": len(chunks), "metadata": metadata, "source": "local_faiss"}
            )
        except Exception as e:
            print(f"[MEMORY] Local Buffer FAILED: {e}")

        # B. Commit to Postgres (If available)
        db: Session = SessionLocal()
        try:
            for i, chunk in enumerate(chunks):
                node = SovereignMemoryNode(
                    content=chunk,
                    metadata_json={**metadata, "timestamp": timestamp},
                    embedding=embeddings[i].tolist()
                )
                db.add(node)
            
            db.commit()
            
            # Update 'synced' flag ONLY after successful commit
            for i in range(len(chunks)):
                self.buffer_metadata[-(len(chunks)-i)]["synced"] = True
            
            self._persist_buffer()
            print(f"[MEMORY] Postgres Commit SUCCESS: Brain synchronized.")
        except Exception as e:
            print(f"[MEMORY] Postgres Commit FAILED (Docker likely offline): {e}")
            db.rollback()
        finally:
            db.close()

    def _chunk_content(self, text: str, max_length: int = 1500) -> List[str]:
        if len(text) <= max_length:
            return [text]
        paragraphs = text.split("\n\n")
        chunks, current_chunk = [], ""
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_length:
                current_chunk += p + "\n\n"
            else:
                if current_chunk: chunks.append(current_chunk.strip())
                if len(p) >= max_length:
                    chunks.append(p[:max_length])
                    current_chunk = ""
                else: current_chunk = p + "\n\n"
        if current_chunk: chunks.append(current_chunk.strip())
        return chunks

    def recall(self, query: str, top_k: int = 5, rerank: bool = True) -> List[Dict[str, Any]]:
        """
        Hybrid Retrieval: Merges Local Buffer + Postgres results.
        """
        candidates = []
        query_vec = None
        
        with self._get_models() as (encoder, reranker):
            query_vec = encoder.encode([query], device=self.device).astype('float32')

            # 1. Pull from Local FAISS
            try:
                if self.index.ntotal > 0:
                    distances, indices = self.index.search(query_vec, min(top_k * 4, self.index.ntotal))
                    for dist, idx in zip(distances[0], indices[0]):
                        if idx < len(self.buffer_metadata):
                            meta = self.buffer_metadata[idx]
                            candidates.append({
                                "content": meta["content"],
                                "metadata": meta["metadata"],
                                "timestamp": meta["metadata"].get("timestamp"),
                                "source": "local_buffer",
                                "vector_score": float(dist)
                            })
            except Exception as e:
                print(f"[MEMORY] Local Recall failed: {e}")

        # 2. Pull from Postgres (If available)
        db: Session = SessionLocal()
        try:
            if query_vec is not None:
                pg_results = db.query(
                    SovereignMemoryNode, 
                    SovereignMemoryNode.embedding.l2_distance(query_vec[0].tolist()).label("distance")
                ).order_by("distance").limit(top_k * 2).all()
                
                for node, distance in pg_results:
                    candidates.append({
                        "content": node.content,
                        "metadata": node.metadata_json,
                        "timestamp": str(node.created_at),
                        "source": "postgres",
                        "vector_score": float(distance)
                    })
        except Exception as e:
            print(f"[MEMORY] Postgres Recall unavailable.")
        finally:
            db.close()

        if not candidates:
            return []

        # 3. De-duplicate (by content fingerprint)
        seen = set()
        unique_candidates = []
        for c in sorted(candidates, key=lambda x: x["vector_score"]):
            if c["content"] not in seen:
                unique_candidates.append(c)
                seen.add(c["content"])

        # 4. Rerank
        if rerank and len(unique_candidates) > 1:
            with self._get_models() as (_, reranker):
                pairs = [[query, c["content"]] for c in unique_candidates[:50]]
                rerank_scores = reranker.predict(pairs)
                for i, score in enumerate(rerank_scores):
                    unique_candidates[i]["score"] = float(score)
                unique_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        else:
            for c in unique_candidates:
                c["score"] = 1.0 - (c["vector_score"] / 100) # Rough normalization

        return unique_candidates[:top_k]

    def sync_with_postgres(self):
        """
        Drains the Local Buffer into Postgres.
        """
        unsynced_items = [(i, meta) for i, meta in enumerate(self.buffer_metadata) if not meta.get("synced", False)]
        if not unsynced_items:
            # print("[MEMORY] No unsynced memories in local buffer.")
            return

        print(f"[MEMORY] Synchronizing {len(unsynced_items)} memories to Postgres...")
        db: Session = SessionLocal()
        success_count = 0
        try:
            for idx, meta in unsynced_items:
                try:
                    # Reconstruction from FAISS can be tricky depending on index type
                    # Using IndexFlatL2 should be fine.
                    embedding = self.index.reconstruct(idx).tolist()

                    node = SovereignMemoryNode(
                        content=meta["content"],
                        metadata_json=meta["metadata"],
                        embedding=embedding
                    )
                    db.add(node)
                    meta["synced"] = True
                    success_count += 1
                except Exception as inner_e:
                    print(f"[MEMORY] Failed to sync item {idx}: {inner_e}")
                    continue
            
            if success_count > 0:
                db.commit()
                self._persist_buffer()
                print(f"[MEMORY] Synchronization COMPLETE: {success_count} entries migrated.")
            else:
                db.rollback()
        except Exception as e:
            print(f"[MEMORY] Global Sync failed: {e}")
            db.rollback()
        finally:
            db.close()

    def save(self): pass

if __name__ == "__main__":
    memory = SovereignMemory()
    memory.commit_to_memory("Hybrid FAISS Memory Test", {"tag": "debug"})
    print(memory.recall("FAISS test"))
