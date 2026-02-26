from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from app.core.agents.visual.agent import VisualAgent

class VisualBuilderSkill(BaseSkill):
    """
    Sovereign Visual Builder Skill (Level 9).
    Wraps the Visual Agent for multi-agent orchestration.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="visual_builder",
            version="2.0.0",
            type="precision",
            description="Autonomous UI/Frontend generator. Use this when the user needs a new page, component, or frontend design. Input: {'prompt': str}",
            tags=["ui", "frontend", "visual", "react", "components"]
        )
        super().__init__(metadata)
        self.visual_agent = VisualAgent()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        prompt = inputs.get("prompt", "")
        
        if not prompt:
            return SkillResult(success=False, output="Error: Visual generation requires a 'prompt' input.", reward=-1.0)
            
        print(f"[SKILL] Invoking Visual Agent for UI generation: {prompt}")
        
        try:
            result = self.visual_agent.run(prompt)
            success = not result.startswith("Visual Agent failed")
            
            return SkillResult(
                success=success,
                output=result,
                reward=10.0 if success else -5.0
            )
        except Exception as e:
            return SkillResult(success=False, output=f"Visual Builder failed: {str(e)}", reward=-5.0)

    def verify(self, result: SkillResult) -> bool:
        return result.success
