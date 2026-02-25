import asyncio
from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from backend.app.agents.env_manager.agent import EnvironmentManager

class EnvironmentManagerSkill(BaseSkill):
    """
    Sovereign Environment Manager Skill (Level 9).
    Wraps the EnvironmentManager agent to handle audits and HITL-guarded terminal execution.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="env_manager",
            version="2.0.0",
            type="precision",
            description="Autonomous infrastructure monitor and executor. Can audit health or execute guarded terminal commands (Level 9 HITL). Inputs: {'action': 'audit' | 'execute', 'command': str, 'target_dir': str}",
            tags=["infrastructure", "monitoring", "terminal", "execution"]
        )
        super().__init__(metadata)
        self.mgr = EnvironmentManager()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        action = inputs.get("action", "audit")
        
        if action == "execute":
            command = inputs.get("command", "")
            target_dir = inputs.get("target_dir", "frontend")
            print(f"[SKILL] Invoking HITL-guarded execution for: {command}")
            
            # Bridge to async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.mgr.execute_command(command, target_dir))
            loop.close()
            
            success = not result.startswith("Error:") and not result.startswith("Execution aborted") and not "Subprocess Error" in result
            return SkillResult(
                success=success,
                output=result,
                reward=10.0 if success else -5.0
            )
            
        else: # Default audit action
            print("[SKILL] Executing Infrastructure Audit (BaaS)...")
            health_report = self.mgr.audit_environment()
            
            success = health_report["status"] == "HEALTHY"
            output = f"Health Status: {health_report['status']}\nResource Utilization: CPU {health_report['resources']['cpu_percent']}%, MEM {health_report['resources']['memory_percent']}%"
            
            return SkillResult(
                success=success,
                output=output,
                reward=5.0 if success else -10.0,
                telemetry=health_report
            )

    def verify(self, result: SkillResult) -> bool:
        return result.success
