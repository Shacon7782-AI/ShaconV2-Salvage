from typing import Dict, Any, List
from ..base import BaseSkill, SkillMetadata, SkillResult
from ...memory.vector_store import SovereignMemory

class RecallSkill(BaseSkill):
    """
    Precision Skill for semantic memory retrieval.
    Allows the agent to 'remember' context from previous tasks.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="sovereign_recall",
            version="1.0.0",
            type="logic",
            description="Semantic retrieval of historical context and system memory.",
            tags=["memory", "context", "recall"]
        )
        super().__init__(metadata)
        self.memory = SovereignMemory()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        Queries the vector store for relevant context.
        Inputs: {"query": str, "top_k": int}
        """
        query = inputs.get("query")
        if not query:
            return SkillResult(success=False, output="Error: Missing 'query' parameter.")
        
        top_k = inputs.get("top_k", 3)
        
        try:
            results = self.memory.recall(query, top_k=top_k)
            
            if not results:
                return SkillResult(
                    success=True, 
                    output="No relevant memories found for this query.",
                    reward=0.5
                )
            
            # Format output for the Orchestrator
            formatted_output = "Retrieved Sovereign Memories:\n"
            for r in results:
                formatted_output += f"- [{r['metadata'].get('phase', 'Unknown')}] {r['content'][:300]}...\n"
            
            return SkillResult(
                success=True,
                output=formatted_output,
                reward=1.0,
                telemetry={"recall_count": len(results)}
            )
            
        except Exception as e:
            return SkillResult(success=False, output=f"Recall Error: {str(e)}", reward=-1.0)

    def verify(self, result: SkillResult) -> bool:
        """Verification is implicit in retrieval success."""
        return result.success
