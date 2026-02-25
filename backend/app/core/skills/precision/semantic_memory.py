from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from app.core.memory.vector_store import SovereignMemory

class SemanticMemorySkill(BaseSkill):
    """
    Sovereign Semantic Memory Skill (VectorRAG).
    Provides the Swarm with long-term semantic retrieval of past operations, code, and decisions.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="semantic_memory",
            version="1.0.0",
            type="precision",
            description="Query the Swarm's long-term semantic memory (Vector DB). Use this to recall how things were built previously or find past code solutions. Input: {'query': str, 'top_k': int}",
            tags=["memory", "vector", "rag", "search", "recall"]
        )
        super().__init__(metadata)
        self.memory = SovereignMemory()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        query = inputs.get("query")
        if not query:
            return SkillResult(success=False, output="Error: 'query' input is required.", reward=-1.0)
            
        top_k = inputs.get("top_k", 3)
        print(f"[SKILL] Querying VectorRAG for semantic match: '{query}'")
        
        try:
            results = self.memory.recall(query, top_k=top_k)
            
            if not results:
                return SkillResult(
                    success=True,
                    output="No relevant insights found in long-term memory.",
                    reward=0.0
                )
                
            formatted_results = "\n\n--- SEMANTIC RECALL RESULTS ---\n"
            for i, res in enumerate(results):
                score = res.get('final_score', res.get('vector_score', 0))
                meta = res.get('metadata', {})
                formatted_results += f"Result {i+1} (Relevance Score: {score:.3f}):\n"
                formatted_results += f"Content: {res.get('content')}\n"
                if meta:
                    formatted_results += f"Context Metadata: {meta}\n"
                formatted_results += "-" * 20 + "\n"
                
            return SkillResult(
                success=True,
                output=formatted_results,
                reward=5.0
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                output=f"Semantic Memory Query Failed: {e}",
                reward=-5.0
            )

    def verify(self, result: SkillResult) -> bool:
        return result.success
