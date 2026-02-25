from typing import Optional, Dict, Any, List
from app.db.schemas.session import SessionLocal
from app.db.schemas.models import ResearchKnowledge
from app.core.memory.vector_store import SovereignMemory

# Initialize Sovereign Memory (Singleton-ish behavior for this module)
# In a full app, this might be injected, but for now we instantiate here.
print("[MEMORY] Initializing Sovereign Memory Connection...")
vector_store = SovereignMemory()

async def check_knowledge(query: str) -> Optional[Dict[str, Any]]:
    """
    Checks the database/vector store for existing research on this topic.
    Uses Semantic Search via SovereignMemory.
    """
    try:
        # 1. Try Semantic Recall first (Sovereign Memory)
        print(f"[MEMORY] recalling: {query}")
        results = vector_store.recall(query, top_k=1)
        
        if results:
            best_hit = results[0]
            # Threshold check (score is L2 distance, lower is better for FAISS FlatL2)
            # But wait, logic depends on distance metric. FlatL2: 0 is identical.
            # Arbitrary threshold for "relevant enough" might be needed.
            # For now, just return the best hit if it exists.
            print(f"[MEMORY] Hit found (score: {best_hit.get('score', 'N/A')})")
            return {
                "title": best_hit.get("metadata", {}).get("title", "Recalled Memory"),
                "url": best_hit.get("metadata", {}).get("url", "memory://vector-store"),
                "snippet": best_hit.get("content", ""),
                "source": "sovereign-memory",
                "created_at": str(best_hit.get("timestamp", ""))
            }
            
        # 2. Fallback to SQL Exact Match (Legacy)
        db = SessionLocal()
        try:
            result = db.query(ResearchKnowledge).filter(ResearchKnowledge.query == query).first()
            if result:
                return {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                    "created_at": result.created_at.isoformat()
                }
        finally:
            db.close()
            
        return None
        
    except Exception as e:
        print(f"[MEMORY] Recall failed: {e}")
        return None

async def save_knowledge(query: str, data: Any) -> bool:
    """
    Saves the research result to the database AND vector memory.
    """
    db = SessionLocal()
    try:
        # Extract details
        summary = "No summary available."
        source_url = "Unknown"
        title = "Research Result"
        
        if isinstance(data, list) and len(data) > 0:
            first_hit = data[0]
            summary = first_hit.get("snippet", "") or first_hit.get("body", "")
            source_url = first_hit.get("url", "") or first_hit.get("href", "")
            title = first_hit.get("title", "Research Result")
            
        # 1. Save to SQL (Structured)
        new_entry = ResearchKnowledge(
            query=query,
            snippet=summary,
            url=source_url,
            source="researcher-agent"
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        
        # 2. Save to Vector Store (Semantic)
        # We embed the summary + query for better retrieval context
        content_to_embed = f"Query: {query}\nResult: {summary}"
        metadata = {
            "query": query,
            "url": source_url,
            "title": title,
            "source": "researcher-agent"
        }
        vector_store.commit_to_memory(content_to_embed, metadata)
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save knowledge: {e}")
        db.rollback()
        return False
    finally:
        db.close()

