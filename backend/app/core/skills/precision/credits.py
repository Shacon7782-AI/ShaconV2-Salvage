from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from ...economy.ledger import SovereignLedger

class CreditSkill(BaseSkill):
    """
    Sovereign Economic Skill.
    Allows agents to query and manage their operational balance.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="credit_management",
            version="1.0.0",
            type="precision",
            description="Interface for querying Sovereign Credits balance and managing agentic operational costs.",
            tags=["economy", "ledger", "L10"]
        )
        super().__init__(metadata)
        self.ledger = SovereignLedger()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        action = inputs.get("action", "query")
        
        if action == "query":
            balance = self.ledger.get_balance()
            output = f"Current Sovereign Balance: {balance} credits."
            return SkillResult(success=True, output=output, reward=1.0, telemetry={"balance": balance})
            
        elif action == "credit":
            amount = inputs.get("amount", 0)
            self.ledger.credit_balance(amount)
            return SkillResult(success=True, output=f"Successfully credited {amount} credits.", reward=1.0)
            
        return SkillResult(success=False, output=f"Unknown action: {action}", reward=-1.0)

    def verify(self, result: SkillResult) -> bool:
        return result.success
