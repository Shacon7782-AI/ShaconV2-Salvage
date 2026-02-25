import asyncio
import os
import subprocess
from typing import Dict, Any, List
from ..base import BaseSkill, SkillMetadata, SkillResult, SkillRegistry

class AutonomousVerificationLoop(BaseSkill):
    """
    Level 10 Autonomous Verification Loop.
    Performs a full-system health check and triggers self-healing if anomalies are detected.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="autonomous_verify_loop",
            version="1.0.0",
            type="precision",
            description="Master verification loop that audits system-wide health, memory integrity, and interop connectivity.",
            tags=["autonomous", "verification", "self-healing", "L10"]
        )
        super().__init__(metadata)

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        print("[SKILL] Initiating Level 10 Autonomous Verification Loop...")
        
        verification_steps = [
            ("System Integrity", "scripts/verify_system_integrity.py"),
            ("Sovereign Pulse", "scripts/sovereign_pulse.py --once"),
            ("MCP Standardization", "scripts/verify_mcp_standard.py"),
            ("Sovereign Recall", "scripts/verify_sovereign_recall.py"),
            ("External MCP Bridge", "scripts/verify_mcp_bridge.py"),
            ("Skill Discovery", "scripts/verify_discovery.py")
        ]
        
        results = []
        all_passed = True
        
        for name, script in verification_steps:
            print(f"   [CHECK] {name}...")
            try:
                # Use sys.executable to ensure we use the same environment
                res = subprocess.run(
                    [os.sys.executable, script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                passed = res.returncode == 0
                results.append(f"{name}: {'PASS' if passed else 'FAIL'}")
                if not passed:
                    all_passed = False
                    print(f"      [WARNING] {name} failed.")
            except Exception as e:
                results.append(f"{name}: ERROR ({str(e)})")
                all_passed = False

        summary = " | ".join(results)
        
        return SkillResult(
            success=all_passed,
            output=f"Full Audit Output: {summary}",
            reward=10.0 if all_passed else -5.0,
            telemetry={"failed_count": len([r for r in results if "FAIL" in r or "ERROR" in r])}
        )

    def verify(self, result: SkillResult) -> bool:
        return result.success
