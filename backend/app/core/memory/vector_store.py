import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy.orm import Session
from app.db.schemas.session import SessionLocal
from app.db.schemas.models import SovereignMemoryNode

class SovereignMemory:
    """
    Persistent Vector Memory for Shacon v2.0 -> v5.0
    Migrated from FAISS to Supabase pgvector for statelessness and scale.
    Uses SentenceTransformers for embeddings and CrossEncoder for reranking.
    """
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2", 
                 storage_dir: Optional[str] = None): # Maintained signature for backwards compat
        self.model_name = model_name
        
        # Initialize ML components
        print(f"[MEMORY] Initializing Sovereign Recall (Model: {model_name}, Backend: pgvector)")
        self.model = SentenceTransformer(model_name)
        # Initialize Cross-Encoder for Reranking
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2') 
        self.dimension = self.model.get_sentence_embedding_dimension()

    def commit_to_memory(self, content: str, metadata: Dict[str, Any]):
        """
        Embeds content, chunks it, and adds it to the Postgres vector store.
        """
        chunks = self._chunk_content(content)
        
        db: Session = SessionLocal()
        try:
            for chunk in chunks:
                embedding = self.model.encode([chunk]).astype('float32')[0].tolist()
                
                # Insert into SovereignMemoryNode (pgvector)
                node = SovereignMemoryNode(
                    content=chunk,
                    metadata_json=metadata,
                    embedding=embedding
                )
                db.add(node)
                
            db.commit()
            print(f"[MEMORY] Committed {len(chunks)} chunks to Postgres vector store.")
        except Exception as e:
            print(f"[MEMORY] Failed to commit to memory: {e}")
            db.rollback()
        finally:
            db.close()

    def _chunk_content(self, text: str, max_length: int = 1500) -> List[str]:
        """Splits long text into semantic chunks."""
        if len(text) <= max_length:
            return [text]
            
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_length:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(p) >= max_length:
                    # Hard truncate if a single block is massive
                    chunks.append(p[:max_length])
                    current_chunk = ""
                else:
                    current_chunk = p + "\n\n"
                    
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def recall(self, query: str, top_k: int = 5, rerank: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves the most semantically relevant memories for a query from Postgres.
        Uses Hybrid RAG: pgvector Retrieval + Cross-Encoder Reranking.
        """
        # Phase 1: pgvector Retrieval (Top 20 for reranking)
        fetch_k = top_k * 4 if rerank else top_k
        query_embedding = self.model.encode([query]).astype('float32')[0].tolist()
        
        db: Session = SessionLocal()
        try:
            # Query db using pgvector's <-> operator (L2 distance)
            # The lower the distance, the more similar they are.
            results = db.query(
                SovereignMemoryNode, 
                SovereignMemoryNode.embedding.l2_distance(query_embedding).label("distance")
            ).order_by("distance").limit(fetch_k).all()
            
            if not results:
                return []
                
            candidates = []
            for node, distance in results:
                candidates.append({
                    "content": node.content,
                    "metadata": node.metadata_json,
                    "timestamp": str(node.created_at),
                    "vector_score": float(distance)  # Distance, lower is better
                })
        except Exception as e:
            print(f"[MEMORY] Recall failed: {e}")
            return []
        finally:
            db.close()
            
        if not rerank or not candidates:
            return candidates[:top_k]

        # --- ADAPTIVE GOVERNANCE: Semantic Fast-Path ---
        # If the best match is extremely close (distance < 0.1), skip reranking
        best_candidate = candidates[0]
        if best_candidate["vector_score"] < 0.1:
            print(f"[MEMORY] ADAPTIVE FAST-PATH: High-confidence vector match ({best_candidate['vector_score']}). Skipping rerank.")
            for c in candidates:
                c["final_score"] = 1.0 - c["vector_score"] # Normalize distance to score (roughly)
                c["score"] = c["final_score"]
            return candidates[:top_k]

        # Phase 2: Cross-Encoder Reranking
        pairs = [[query, c["content"]] for c in candidates]
        rerank_scores = self.reranker.predict(pairs)
        
        # Attach rerank scores and sort
        for i, score in enumerate(rerank_scores):
            candidates[i]["rerank_score"] = float(score)
            candidates[i]["final_score"] = float(score) 
            candidates[i]["score"] = float(score) # legacy compat
            
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        
        return candidates[:top_k]

    def save(self):
        """Legacy. Postgres saves automatically on commit."""
        pass

if __name__ == "__main__":
    # Internal test
    memory = SovereignMemory()
    memory.commit_to_memory("Phase 6 was about MCP standardization.", {"phase": 6})
    memories = memory.recall("What happened in the previous phase?")
    for m in memories:
        print(f"Recall: {m['content']} (Score: {m.get('score', m.get('vector_score'))})")
