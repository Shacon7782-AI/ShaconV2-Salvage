import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
# Assuming SwarmLLMRouter is moved to the new backend, or we can mock it for now.
# In a fresh start we might just use LangChain chat models directly.
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.core.skills.base import SkillRegistry
from backend.app.core.memory.vector_store import SovereignMemory
from backend.app.core.agents.base import BaseAgent

class OrchestrationStep(BaseModel):
    thinking: str = Field(description="Internal reasoning for this step")
    action: str = Field(description="The action to take: 'DISCUSS', 'EXECUTE_SKILL', or 'COMPLETE'")
    skill_name: Optional[str] = Field(default=None, description="Name of the skill if action is 'EXECUTE_SKILL'")
    skill_input: Optional[Dict[str, Any]] = Field(default=None, description="Arguments for the skill")
    discussion_prompt: Optional[str] = Field(default=None, description="Prompt for the user if action is 'DISCUSS'")

class Orchestrator(BaseAgent):
    """
    The High-Level Brain of ShaconV2 Workspace.
    Transitions between Discussion and Execution modes.
    Cleaned of background Sentinel/Evaluator loops.
    """
    def __init__(self, registry: SkillRegistry, sovereign_memory: SovereignMemory, mock: bool = False):
        super().__init__(agent_id="Orchestrator")
        self.registry = registry
        self.sovereign_memory = sovereign_memory
        self.mock = mock
        self.memory: List[Dict[str, Any]] = []
        self.max_steps = 10
        self.step_counter = 0

        # We will use Gemini Pro as the default structured LLM for V2.
        self.structured_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro").with_structured_output(OrchestrationStep)

    async def reason(self, user_intent: str, chat_history: List[Dict[str, str]] = []) -> OrchestrationStep:
        """
        Main reasoning loop. Cleaned up, fully async, and direct.
        """
        if self.mock:
            return OrchestrationStep(
                thinking="Diagnostic mock mode running clean.",
                action="DISCUSS",
                discussion_prompt="I am currently in Diagnostic Mock Mode. How can I help you?"
            )

        if self.step_counter >= self.max_steps:
            return OrchestrationStep(
                thinking=f"Halted at max steps ({self.max_steps}).",
                action="COMPLETE"
            )

        available_skills = self.registry.list_skills()
        skills_summary = "\n".join([f"- {s.name}: {s.description}" for s in available_skills])

        historical_context = "None"
        try:
            memories = self.sovereign_memory.recall(user_intent, top_k=2)
            if memories:
                historical_context = "\n".join([f"- {m['content']}" for m in memories])
        except Exception as e:
            print(f"[MEMORY] Recall failed: {e}")

        execution_context = "\n".join([
            f"STEP {i+1}: Action={m.get('action')}, Result={m.get('result', 'N/A')}" 
            for i, m in enumerate(self.memory)
        ])
        
        system_instructions = self.get_base_system_prompt()
        prompt_content = f"""{system_instructions}
            
            HISTORICAL CONTEXT (SAVED MEMORY):
            {{history_context}}

            AVAILABLE SKILLS:
            {{skills}}
            
            MODES:
            - DISCUSS: Use this to clarify intent, propose a plan, or ask for feedback.
            - EXECUTE_SKILL: Use this to fire off a tool.
            - COMPLETE: Use this when the goal is achieved.
            """

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_content),
            ("human", """User Intent: {intent}
            
            CHAT HISTORY: {history}
            
            EXECUTION CONTEXT: {context}
            """)
        ])

        chain = prompt | self.structured_llm
        step = chain.invoke({
            "intent": user_intent,
            "skills": skills_summary,
            "history_context": historical_context,
            "history": json.dumps(chat_history) if chat_history else "None",
            "context": execution_context if execution_context else "None"
        })
        
        return step

    async def execute_step(self, step: OrchestrationStep) -> Dict[str, Any]:
        """
        Executes the step cleanly as a regular async function.
        """
        self.step_counter += 1
        result_data = {"action": step.action, "thinking": step.thinking}
        
        if step.action == "EXECUTE_SKILL":
            skill = self.registry.get_skill(step.skill_name)
            if not skill:
                res = {"error": f"Skill {step.skill_name} not found"}
            else:
                async def run_skill():
                    return skill.execute(step.skill_input or {})

                try:
                    skill_res = await self.execute_action(run_skill)
                    
                    if isinstance(skill_res, dict) and skill_res.get("status") == "ERROR":
                        res = skill_res
                    else:
                        res = skill_res.dict() if hasattr(skill_res, "dict") else {"result": str(skill_res)}
                        if getattr(skill_res, "success", True):
                            content = f"Skill {step.skill_name} Output: {str(getattr(skill_res, 'output', res))[:500]}"
                            self.sovereign_memory.commit_to_memory(content, {"skill": step.skill_name, "type": "skill_result"})
                except Exception as e:
                    res = {"error": f"Execution Failed: {e}"}

            result_data["result"] = res
            self.memory.append(result_data)
            return res
        
        elif step.action == "DISCUSS":
            result_data["prompt"] = step.discussion_prompt
            self.memory.append(result_data)
            self.sovereign_memory.commit_to_memory(f"Discussion: {step.discussion_prompt}", {"type": "discussion"})
            return {"mode": "DISCUSSION", "prompt": step.discussion_prompt}
            
        elif step.action == "COMPLETE":
            summary = f"Mission Complete. {step.thinking}"
            self.sovereign_memory.commit_to_memory(summary, {"type": "mission_completion"})
            result_data["status"] = "COMPLETE"
            self.memory.append(result_data)
            return {"mode": "IDLE", "status": "Goal achieved", "thinking": step.thinking}
            
        return {"mode": "IDLE", "status": "Goal achieved or stopped"}

    def reset_memory(self):
        self.memory = []
        self.step_counter = 0

