import json
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
# Assuming SwarmLLMRouter is moved to the new backend, or we can mock it for now.
# In a fresh start we might just use LangChain chat models directly.
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.skills.base import SkillRegistry
from app.core.memory.vector_store import SovereignMemory
from app.core.agents.base import BaseAgent, GovernedAgent
from app.core.telemetry import Blackboard
from app.core.triage import SovereignTriage

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
    __slots__ = (
        "registry", 
        "sovereign_memory", 
        "mock", 
        "blackboard", 
        "memory", 
        "max_steps", 
        "step_counter", 
        "structured_llm"
    )

    def __init__(self, registry: SkillRegistry, sovereign_memory: SovereignMemory, mock: bool = False):
        super().__init__(agent_id="Orchestrator")
        self.registry = registry
        self.sovereign_memory = sovereign_memory
        self.mock = mock
        self.blackboard = Blackboard()
        self.memory: List[Dict[str, Any]] = []
        self.max_steps = 10
        self.step_counter = 0
        self.triage = SovereignTriage()

        # Defer initialization to avoid Pydantic clashes during boot in mock mode.
        self.structured_llm = None
        if not self.mock:
            from app.core.llm_router import SwarmLLMRouter
            self.structured_llm = SwarmLLMRouter.get_optimal_llm(
                structured_schema=OrchestrationStep,
                complexity="HIGH"
            )

    async def recover_state(self, task_id: str):
        """Resumes agent state from a durable checkpoint."""
        from app.core.memory.durable_execution import DurableContext
        state = DurableContext.recover(task_id)
        if state:
            self.step_counter = state.get("step", 0)
            # We could also restore history/memory if needed
            print(f"[{self.agent_id}] Recovered to Step {self.step_counter}.")
            return True
        return False

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

        # 16-Phase Protocol: Phase 1-6 Triage
        triage_result = await self.triage.execute_triage(user_intent)
        
        # Librarian Pattern: JIT Skill Loading
        for skill_name in triage_result.required_skills:
            # Note: Using GovernedAgent logic to load library skills
            # (Currently GovernedAgent is in base.py, but we can assume Orchestrator has similar capability)
            if skill_name not in self.registry._skills:
                self.registry.load_exclusive_skill(skill_name)

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

        # Synthesize Blackboard Insights
        insights = self.blackboard.get_recent_insights(limit=3)
        system_insights = "None"
        if insights:
            system_insights = "\n".join([f"- [{i['agent_id']}] {i['content']}" for i in insights])
        
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

            SYSTEM INSIGHTS (INTERNAL HEALTH):
            {system_insights}

            IMPORTANT: RETURN YOUR RESPONSE AS A VALID JSON OBJECT MATCHING THE SCHEMA.
            DO NOT INCLUDE ANY TEXT OUTSIDE THE JSON BLOCK.
            """

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_content),
            ("human", """User Intent: {intent}
            
            CHAT HISTORY: {history}
            
            EXECUTION CONTEXT: {context}
            """)
        ])

        if self.structured_llm:
            try:
                print(f"[ORCHESTRATOR] Reasoning with {self.agent_id}...")
                chain = prompt | self.structured_llm
                step = await chain.ainvoke({
                    "intent": user_intent,
                    "skills": skills_summary,
                    "history_context": historical_context,
                    "system_insights": system_insights,
                    "history": json.dumps(chat_history) if chat_history else "None",
                    "context": execution_context if execution_context else "None"
                })
                
                # Handle cases where the LLM might return a dictionary instead of a Pydantic object
                if isinstance(step, dict):
                    return OrchestrationStep(**step)
                
                # Defensive check for expected attributes
                if not hasattr(step, "action") or isinstance(step, (str, dict)):
                    print(f"[ORCHESTRATOR] Unexpected response type: {type(step)}")
                    content = str(getattr(step, "content", step))
                    print(f"[ORCHESTRATOR] Raw Content Snapshot: {content[:500]}...")
                    
                    if "{" in content:
                        try:
                            start = content.find("{")
                            end = content.rfind("}") + 1
                            json_str = content[start:end]
                            import json
                            data = json.loads(json_str)
                            print(f"[ORCHESTRATOR] Extracted JSON from content.")
                            return OrchestrationStep(**data)
                        except Exception as e:
                            print(f"[ORCHESTRATOR] Manual JSON parsing failed: {e}")

                    if isinstance(step, dict):
                        try:
                            return OrchestrationStep(**step)
                        except Exception as e:
                            print(f"[ORCHESTRATOR] Dict conversion failed: {e}")

                    raise ValueError(f"LLM returned an invalid response type: {type(step)}")

                return step
            except Exception as e:
                print(f"[ORCHESTRATOR] Reasoning failed: {e}")
                return OrchestrationStep(
                    thinking=f"Reasoning process encountered an error: {e}",
                    action="DISCUSS",
                    discussion_prompt="I apologize, but I encountered an internal reasoning error. How can I assist you otherwise?"
                )
        else:
            return OrchestrationStep(
                thinking="LLM not initialized.",
                action="DISCUSS",
                discussion_prompt="Critical Error: Structured LLM pipeline not initialized."
            )

    async def execute_step(self, step: OrchestrationStep) -> Dict[str, Any]:
        """
        Executes the step cleanly as a regular async function with Durable Checkpointing.
        """
        self.step_counter += 1
        
        # Durable Checkpoint: Phase 12-14 Logic
        # (Assuming we have a task_id session; using self.agent_id for now)
        from app.core.memory.durable_execution import DurableContext
        durable = DurableContext(task_id=f"TASK_{self.agent_id}_{self.step_counter}")
        durable.checkpoint(step_name=step.action, data={"thinking": step.thinking})

        result_data = {"action": step.action, "thinking": step.thinking}
        
        if step.action == "EXECUTE_SKILL":
            skill = self.registry.get_skill(step.skill_name)
            if not skill:
                res = {"error": f"Skill {step.skill_name} not found"}
            else:
                async def run_skill():
                    res = skill.execute(step.skill_input or {})
                    if asyncio.iscoroutine(res):
                        return await res
                    return res

                try:
                    skill_res = await self.execute_action(run_skill)
                    
                    if isinstance(skill_res, dict) and skill_res.get("status") == "ERROR":
                        res = skill_res
                    else:
                        res = skill_res.dict() if hasattr(skill_res, "dict") else {"result": str(skill_res)}
                        if getattr(skill_res, "success", True):
                            content = f"Skill {step.skill_name} Output: {str(getattr(skill_res, 'output', res))[:500]}"
                            self.sovereign_memory.commit_to_memory(content, {"skill": step.skill_name, "type": "skill_result"})
                            
                            # Phase 12-16 Triage Validation
                            await self.triage.execute_post_execution_triage(f"TASK_{self.agent_id}_{self.step_counter}", res)
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

