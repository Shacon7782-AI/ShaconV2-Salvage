import asyncio
from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from backend.app.agents.researcher.agent import ResearchAgent

class DeepResearchSkill(BaseSkill):
    """
    Precision Skill for autonomous deep research.
    Wraps the core ResearchAgent logic.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="deep_research",
            version="1.1.0",
            type="precision",
            description="Performs autonomous multi-source research on complex technical or strategic topics.",
            tags=["research", "knowledge", "intelligence"]
        )
        super().__init__(metadata)
        self.agent = ResearchAgent()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        query = inputs.get("query")
        if not query:
            return SkillResult(success=False, output="Missing query parameter", reward=-1.0)
            
        print(f"[SKILL] Executing Deep Research for: {query}")
        
        try:
            # ResearchAgent is typically async, we run it in a loop if needed or assume sync wrapper
            # For this precision layer, we use the agent's run method
            result = asyncio.run(self.agent.run(query))
            
            success = "error" not in result
            
            return SkillResult(
                success=success,
                output=result.get("summary", "No summary found") if success else result.get("error"),
                reward=2.0 if success else -1.0,
                telemetry={
                    "sources": len(result.get("sources", [])),
                    "execution_time": result.get("time_taken", 0)
                }
            )
        except Exception as e:
            return SkillResult(
                success=False,
                output=str(e),
                reward=-5.0,
                telemetry={"error": "Research execution failed"}
            )

    def verify(self, result: SkillResult) -> bool:
        # Verify that the output is substantial (e.g., more than 100 characters)
        return len(result.output) > 100 if result.success else False
