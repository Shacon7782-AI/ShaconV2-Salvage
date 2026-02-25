"""
Provider Router - Maps query types to optimal search provider order.

Sovereign Law: Intelligent routing maximizes search quality while respecting quotas.
"""

from typing import List
from .query_classifier import QueryClassifier


# Provider specializations based on research:
# - Serper: Fast Google results, good for code/news/general
# - Tavily: AI-optimized, returns content extracts, best for research
# - Exa: Neural/semantic search, best for technical/academic content
# - SearchApi: Rich Google SERP data, good for comprehensive results
# - Google: Official results (when billing enabled)
# - DuckDuckGo: Privacy-focused fallback

ROUTING_RULES = {
    "code": ["serper", "exa", "searchapi", "tavily", "google", "duckduckgo"],
    "news": ["serper", "searchapi", "tavily", "google", "duckduckgo"],
    "research": ["tavily", "exa", "serper", "searchapi", "google", "duckduckgo"],
    "technical": ["exa", "tavily", "serper", "searchapi", "google", "duckduckgo"],
    "general": ["serper", "tavily", "exa", "searchapi", "google", "duckduckgo"],
}


class ProviderRouter:
    """
    Routes queries to optimal search providers based on query type.
    """
    
    def __init__(self):
        self.classifier = QueryClassifier()
    
    def get_provider_order(self, query: str) -> List[str]:
        """
        Get the optimal provider order for a query.
        
        Args:
            query: The search query
            
        Returns:
            List of provider names in priority order
        """
        query_type, confidence = self.classifier.classify(query)
        
        print(f"[ProviderRouter] Query classified as '{query_type}' (confidence: {confidence:.2f})")
        
        return ROUTING_RULES.get(query_type, ROUTING_RULES["general"])
    
    def get_query_info(self, query: str) -> dict:
        """
        Get detailed routing info for a query (for debugging/logging).
        """
        query_type, confidence = self.classifier.classify(query)
        all_scores = self.classifier.get_all_scores(query)
        
        return {
            "query": query,
            "classified_as": query_type,
            "confidence": confidence,
            "all_scores": all_scores,
            "provider_order": ROUTING_RULES.get(query_type, ROUTING_RULES["general"])
        }
