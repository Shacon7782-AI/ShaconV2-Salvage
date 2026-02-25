import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.core.agents.orchestrator.agent import Orchestrator
from app.core.skills.base import SkillRegistry
from app.core.skills.precision.deep_research import DeepResearchSkill
from app.core.memory.vector_store import SovereignMemory

async def test_orchestrator():
    print("--- Testing Orchestrator ---")
    
    registry = SkillRegistry()
    registry.register(DeepResearchSkill())
    memory = SovereignMemory()
    orchestrator = Orchestrator(registry=registry, sovereign_memory=memory, mock=False)
    
    intent = "Research the latest advancements in quantum computing"
    print(f"Intent: {intent}")
    
    # 1. Reason
    step = await orchestrator.reason(intent, [])
    print(f"Reasoning: {step.thinking}")
    print(f"Action: {step.action}")
    print(f"Skill: {step.skill_name}")
    
    # 2. Execute
    print("\nExecuting Step...")
    result = await orchestrator.execute_step(step)
    
    print("\nExecution Result Keys:")
    print(list(result.keys()))
    if "result" in result:
       print("Result preview:", str(result["result"])[:200])
    
if __name__ == "__main__":
    asyncio.run(test_orchestrator())
