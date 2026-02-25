import subprocess
import os
from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult

class SystemIntegritySkill(BaseSkill):
    """
    Precision Skill that wraps the 'verify_system_integrity.py' script.
    Provides formal verification of the sovereign workspace state.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="system_integrity_verify",
            version="1.0.0",
            type="precision",
            description="Performs deep integrity checks on core protocols, environment variables, and filesystem structure.",
            tags=["verification", "security", "integrity"]
        )
        super().__init__(metadata)

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        print(f"[SKILL] Executing System Integrity Verification...")
        
        script_path = os.path.join(os.getcwd(), "scripts", "verify_system_integrity.py")
        
        try:
            # Run the legacy script and capture output
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            success = result.returncode == 0
            
            # Formalize the result for the Orchestrator
            return SkillResult(
                success=success,
                output=result.stdout if success else result.stderr,
                reward=1.0 if success else -1.0,
                telemetry={
                    "return_code": result.returncode,
                    "script": "verify_system_integrity.py",
                    "timestamp": os.path.getmtime(script_path) if os.path.exists(script_path) else 0
                }
            )
        except Exception as e:
            return SkillResult(
                success=False,
                output=str(e),
                reward=-5.0,
                telemetry={"error": "Skill execution failure"}
            )

    def verify(self, result: SkillResult) -> bool:
        # Precision verification: ensure the output contains the 'Sovereign Handshake' confirmation
        return "Sovereign Handshake: OK" in result.output if result.success else False
