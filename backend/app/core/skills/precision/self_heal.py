import os
import subprocess
from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from core_protocol.self_heal_protocol import SelfHealer
from backend.app.telemetry.blackboard import Blackboard

class SelfHealSkill(BaseSkill):
    """
    Precision Skill for autonomous system repair.
    Wraps the SelfHealer protocol to monitor critical files and perform Git rollbacks.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="self_heal",
            version="2.0.0",
            type="precision",
            description="Autonomous system repair. Scans for file drift or performs 'revert_commit' to rollback broken deployments. Inputs: {'action': 'scan' | 'revert_commit'}",
            tags=["security", "repair", "integrity", "git"]
        )
        super().__init__(metadata)
        self.healer = SelfHealer(os.getcwd())
        self.blackboard = Blackboard()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        action = inputs.get("action", "scan")
        
        if action == "revert_commit":
            return self._execute_git_revert()
            
        print(f"[SKILL] Initiating Self-Heal Scan...")
        
        try:
            drifted_files = self.healer.scan_for_drift()
            
            if not drifted_files:
                return SkillResult(
                    success=True,
                    output="System Integrity is 100%. No drift detected.",
                    reward=1.0,
                    telemetry={"drift_count": 0}
                )
            
            # Heal the system
            self.healer.heal(drifted_files)
            
            return SkillResult(
                success=True,
                output=f"Integrity Breach detected in {len(drifted_files)} files. System successfully healed.",
                reward=2.0,
                telemetry={
                    "drift_count": len(drifted_files),
                    "repaired_files": drifted_files
                }
            )
        except Exception as e:
            return SkillResult(
                success=False,
                output=str(e),
                reward=-5.0,
                telemetry={"error": "Self-heal execution failed"}
            )

    def _execute_git_revert(self) -> SkillResult:
        """Iron Dome trigger for continuous deployment failures."""
        print("[SELF_HEAL] Iron Dome Triggered: Reverting latest commit.")
        try:
            # Revert the latest commit without committing immediately
            subprocess.run(["git", "revert", "--no-commit", "HEAD"], check=True, capture_output=True)
            # Commit the revert
            commit_msg = "fix(iron-dome): auto-revert broken deployment [skip ci]"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
            # Push changes
            subprocess.run(["git", "push"], check=True, capture_output=True)
            
            post_mortem = "Iron Dome activated. Latest commit reverted and pushed. Deployments should recover shortly."
            self.blackboard.post_finding("SelfHeal", post_mortem, related_mission_id="iron_dome")
            
            return SkillResult(success=True, output=post_mortem, reward=10.0)
            
        except subprocess.CalledProcessError as e:
            msg = f"Git revert failed:\nStdout: {e.stdout.decode() if e.stdout else 'None'}\nStderr: {e.stderr.decode() if e.stderr else 'None'}"
            self.blackboard.post_finding("SelfHeal", msg, related_mission_id="iron_dome")
            # Abort the failed revert
            try:
                subprocess.run(["git", "revert", "--abort"], capture_output=True)
            except Exception:
                pass
            return SkillResult(success=False, output=msg, reward=-5.0)

    def verify(self, result: SkillResult) -> bool:
        # Final verification via a second scan
        drift = self.healer.scan_for_drift()
        return len(drift) == 0 if result.success else False
