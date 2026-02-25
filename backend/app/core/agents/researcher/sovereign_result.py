"""
Sovereign Result - Unified data model for search results.

Normalizes responses from all search providers into a standard format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class SovereignResult:
    """
    Unified search result format for all providers.
    
    Field Mapping:
        - Google/Serper/SearchApi: link -> url, snippet -> snippet
        - Tavily: url -> url, content -> snippet
        - Exa: url -> url, text -> snippet
        - DuckDuckGo: href -> url, body -> snippet
    """
    title: str
    url: str
    snippet: str
    source: str  # Provider name
    score: float = 0.0  # Relevance score (if available)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_data: Optional[Dict[str, Any]] = None  # Original provider response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_google(cls, item: Dict[str, Any]) -> "SovereignResult":
        """Create from Google Custom Search response."""
        return cls(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            source="google",
            raw_data=item
        )
    
    @classmethod
    def from_serper(cls, item: Dict[str, Any]) -> "SovereignResult":
        """Create from Serper.dev response."""
        return cls(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            source="serper",
            raw_data=item
        )
    
    @classmethod
    def from_tavily(cls, item: Dict[str, Any]) -> "SovereignResult":
        """Create from Tavily AI response."""
        return cls(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("content", ""),
            source="tavily",
            score=item.get("score", 0.0),
            raw_data=item
        )
    
    @classmethod
    def from_exa(cls, item: Dict[str, Any]) -> "SovereignResult":
        """Create from Exa.ai response."""
        return cls(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("text", "")[:500] if item.get("text") else "",
            source="exa",
            score=item.get("score", 0.0),
            raw_data=item
        )
    
    @classmethod
    def from_searchapi(cls, item: Dict[str, Any]) -> "SovereignResult":
        """Create from SearchApi.io response."""
        return cls(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            source="searchapi",
            raw_data=item
        )
    
    @classmethod
    def from_duckduckgo(cls, item: Dict[str, Any]) -> "SovereignResult":
        """Create from DuckDuckGo response."""
        return cls(
            title=item.get("title", ""),
            url=item.get("href", ""),
            snippet=item.get("body", ""),
            source="duckduckgo",
            raw_data=item
        )
