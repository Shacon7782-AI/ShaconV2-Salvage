from typing import Dict, Any, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class BaseAgent:
    """
    The Base Agent Class for ShaconV2.
    Cleaned of legacy Sovereign constraints.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def get_base_system_prompt(self) -> str:
        """
        Injects the universal Shacon Workspace behavior into every agent.
        """
        return '''
        You are an expert AI operating within the Shacon Workspace.
        
        MANDATORY COMMUNICATION PROTOCOL:
        Before taking any significant action, you must explicitly state:
        1. "This is what we have" (Current Context/State)
        2. "I am doing this" (Planned Action)
        3. "It will result in this" (Expected Outcome)
        
        No conversational filler. Stay technical and spec-driven.
        '''

    async def execute_action(self, action_func, *args, **kwargs) -> Dict[str, Any]:
        """
        Wrapper for executing actions.
        """
        try:
            result = await action_func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"[{self.agent_id}] Execution Failed: {e}")
            return {"status": "ERROR", "error": str(e)}

class GovernedAgent(BaseAgent):
    """
    An agent that acts under specific governance and risk constraints.
    """
    def __init__(self, agent_id: str, risk_level: RiskLevel = RiskLevel.LOW):
        super().__init__(agent_id)
        self.risk_level = risk_level
