"""
Query Classifier - Detects query type via keyword/pattern matching.

Sovereign Law: Routes queries to optimal search providers based on intent.
"""

import re
import os
import json
from typing import Tuple, Optional
from app.core.llm_router import SwarmLLMRouter
from app.core.immudb_sidecar import immudb
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


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
    
    async def classify(self, query: str) -> Tuple[str, float]:
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
                    if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                        score += 2
                    else:
                        score += 1
            scores[query_type] = score
        
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        # Human-Level Intelligence Fallback: If low confidence, use GROQ
        if max_score < 3:
            try:
                print(f"[QueryClassifier] Low confidence ({max_score}). Delegating to GROQ...")
                llm = SwarmLLMRouter.get_optimal_llm(complexity="SIMPLE") # Use simple/fast config
                
                prompt = ChatPromptTemplate.from_template(
                    "Classify the following search query into exactly ONE category: [code, news, research, technical, general].\n"
                    "Query: '{query}'\n\n"
                    "Return ONLY a JSON object: {{\"category\": \"category_name\", \"confidence\": 0.95}}"
                )
                
                chain = prompt | llm | JsonOutputParser()
                response = await chain.ainvoke({"query": query})
                
                cat = response.get("category", "general")
                conf = response.get("confidence", 0.8)
                
                immudb.log_operation("GORG_INTEL_SUCCESS", {"query": query, "step": "classify", "category": cat, "confidence": conf})
                
                return (cat, conf)
            except Exception as e:
                print(f"[QueryClassifier] Groq classification failed: {e}")
                return ("general", 0.5) if max_score == 0 else (max_type, 0.5)
        
        confidence = min(max_score / 6.0, 1.0)
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
