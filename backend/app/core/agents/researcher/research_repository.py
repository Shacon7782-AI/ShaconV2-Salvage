"""
Research Repository - Persistence layer for Sovereign Memory

Handles storage and retrieval of search results with deduplication.
"""

import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db.schemas.models import ResearchKnowledge


class ResearchRepository:
    """
    Repository for storing and retrieving research results.
    
    Features:
    - URL-based deduplication
    - Query caching (reuse results within TTL)
    - Provider-agnostic storage
    """
    
    # Cache TTL: Results older than this are considered stale
    CACHE_TTL_HOURS = 24
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def hash_url(url: str) -> str:
        """Generate a hash for URL deduplication."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def find_cached_results(self, query: str, max_age_hours: int = None) -> List[ResearchKnowledge]:
        """
        Find cached results for a query.
        
        Args:
            query: Search query
            max_age_hours: Maximum age of results (default: CACHE_TTL_HOURS)
            
        Returns:
            List of cached ResearchKnowledge entries
        """
        if max_age_hours is None:
            max_age_hours = self.CACHE_TTL_HOURS
            
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        return self.db.query(ResearchKnowledge).filter(
            ResearchKnowledge.query == query,
            ResearchKnowledge.created_at >= cutoff
        ).order_by(desc(ResearchKnowledge.created_at)).all()
    
    def store_results(
        self, 
        query: str, 
        query_type: str,
        results: List[Dict[str, Any]]
    ) -> int:
        """
        Store search results with deduplication.
        
        Args:
            query: Original search query
            query_type: Classified query type (code, news, etc.)
            results: List of result dicts with title, url, snippet, source
            
        Returns:
            Number of new results stored (excludes duplicates)
        """
        stored_count = 0
        
        for result in results:
            url = result.get("url", "")
            if not url:
                continue
                
            url_hash = self.hash_url(url)
            
            # Check for duplicate URL
            existing = self.db.query(ResearchKnowledge).filter(
                ResearchKnowledge.url_hash == url_hash
            ).first()
            
            if existing:
                continue  # Skip duplicate
            
            # Create new entry
            entry = ResearchKnowledge(
                query=query,
                query_type=query_type,
                source=result.get("source", "unknown"),
                title=result.get("title", ""),
                url=url,
                url_hash=url_hash,
                snippet=result.get("snippet", ""),
                score=str(result.get("score", 0.0))
            )
            
            self.db.add(entry)
            stored_count += 1
        
        if stored_count > 0:
            self.db.commit()
            print(f"[ResearchRepository] Stored {stored_count} new results for query: {query}")
        
        return stored_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total = self.db.query(ResearchKnowledge).count()
        
        # Count by source
        sources = {}
        for source in ["serper", "tavily", "exa", "searchapi", "google", "duckduckgo"]:
            count = self.db.query(ResearchKnowledge).filter(
                ResearchKnowledge.source == source
            ).count()
            if count > 0:
                sources[source] = count
        
        return {
            "total_entries": total,
            "by_source": sources
        }
