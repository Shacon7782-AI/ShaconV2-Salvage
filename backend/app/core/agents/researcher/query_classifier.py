"""
Query Classifier - Detects query type via keyword/pattern matching.

Sovereign Law: Routes queries to optimal search providers based on intent.
"""

import re
from typing import Tuple


class QueryClassifier:
    """
    Classifies queries into types: code, news, research, technical, general.
    Used by ProviderRouter to select optimal search providers.
    """
    
    PATTERNS = {
        "code": [
            "python", "javascript", "java", "typescript", "rust", "golang", "c++",
            "function", "class", "method", "error", "exception", "bug", "debug",
            "stackoverflow", "github", "npm", "pip", "import", "library",
            "syntax", "compile", "runtime", "async", "await", "promise",
            "api", "sdk", "framework", "react", "vue", "angular", "django", "flask"
        ],
        "news": [
            "latest", "today", "yesterday", "breaking", "update", "announce",
            "release", "launch", "2024", "2025", "2026", "this week", "this month",
            "recent", "new", "just", "now", "happening"
        ],
        "research": [
            "study", "paper", "research", "analysis", "comparison", "academic",
            "thesis", "journal", "peer-reviewed", "citation", "methodology",
            "hypothesis", "data", "statistics", "findings", "conclusion",
            "literature", "review", "survey", "meta-analysis"
        ],
        "technical": [
            "documentation", "docs", "how to", "tutorial", "guide", "setup",
            "install", "configure", "deploy", "architecture", "design pattern",
            "best practice", "specification", "reference", "manual"
        ]
    }
    
    def classify(self, query: str) -> Tuple[str, float]:
        """
        Classify a query into a type.
        
        Returns:
            Tuple of (query_type, confidence_score)
            Types: "code", "news", "research", "technical", "general"
        """
        query_lower = query.lower()
        scores = {}
        
        for query_type, keywords in self.PATTERNS.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Exact word match scores higher
                    if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                        score += 2
                    else:
                        score += 1
            scores[query_type] = score
        
        # Find the highest scoring type
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        # If no patterns matched, return general
        if max_score == 0:
            return ("general", 0.5)
        
        # Calculate confidence (normalize to 0-1 range)
        confidence = min(max_score / 6.0, 1.0)  # 6 matches = 100% confidence
        
        return (max_type, confidence)
    
    def get_all_scores(self, query: str) -> dict:
        """Get scores for all query types (for debugging)."""
        query_lower = query.lower()
        scores = {}
        
        for query_type, keywords in self.PATTERNS.items():
            score = 0
            matched = []
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
                    matched.append(keyword)
            scores[query_type] = {"score": score, "matched": matched}
        
        return scores
