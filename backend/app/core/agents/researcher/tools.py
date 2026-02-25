from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.agents.researcher.search_aggregator import SearchAggregator
from app.db.schemas.session import SessionLocal
from app.db.schemas.models import ResearchKnowledge

async def perform_search(query: str, force_fresh: bool = False) -> List[Dict[str, Any]]:
    """
    Executes a search with Sovereign Memory caching.
    1. Check DB for existing results (Art. VII State).
    2. If found & !force, return cached (Efficiency).
    3. If not, Search -> Persist -> Return.
    """
    db: Session = SessionLocal()
    try:
        # 1. State: Check Memory
        if not force_fresh:
            cached = db.query(ResearchKnowledge).filter(ResearchKnowledge.query == query).all()
            if cached:
                print(f"[TOOL] Found {len(cached)} cached results for: {query}")
                return [{
                    "title": c.title,
                    "url": c.url,
                    "snippet": c.snippet,
                    "source": c.source
                } for c in cached]

        # 2. Action: Execute Search
        aggregator = SearchAggregator()
        results = await aggregator.search(query)
        
        # 3. Result: Persist Memory
        if results:
            for r in results:
                # Avoid duplicates in the same query batch
                exists = db.query(ResearchKnowledge).filter(
                    ResearchKnowledge.query == query,
                    ResearchKnowledge.url == r["url"]
                ).first()
                
                if not exists:
                    knowledge = ResearchKnowledge(
                        query=query,
                        source=r["source"],
                        title=r["title"],
                        url=r["url"],
                        snippet=r["snippet"]
                    )
                    db.add(knowledge)
            db.commit()
            print(f"[TOOL] Persisted {len(results)} new results for: {query}")

        return results
    finally:
        db.close()
