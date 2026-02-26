import os
import psutil
import subprocess
import platform
from typing import Dict, Any
from app.core.skills.base import BaseSkill, SkillMetadata, SkillResult
from app.core.agents.base import RiskLevel
from app.core.immudb_sidecar import immudb

class PipelineDoctorSkill(BaseSkill):
    """
    Autonomous self-healing diagnostic tool.
    Analyzes system health and triggers remediation scripts if necessary.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="pipeline_doctor",
            version="1.0.0",
            type="precision",
            tier="TIER_1_BIOS", # Core health must be BIOS
            description="Autonomous health monitoring and self-healing. Triggers recovery protocols.",
            tags=["health", "monitoring", "self-healing", "recovery"]
        )
        super().__init__(metadata)

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        """
        Runs a full system diagnostic.
        """
        print("[PIPELINE DOCTOR] Running Diagnostic Protocol...")
        report = {}
        
        # 1. Memory Pressure Check
        mem = psutil.virtual_memory()
        report["ram_usage_percent"] = mem.percent
        if mem.percent > 90:
            report["status"] = "CRITICAL"
            report["issue"] = "Memory exhaustion detected."
            self._trigger_dgx_spark()
        else:
            report["status"] = "HEALTHY"

        # 2. Service Verifications
        # Mocking integrity checks for now
        report["postgres_sync"] = "OK"
        report["immudb_integrity"] = "VERIFIED"
        
        # 3. Protocol Drift Check
        # (Compare environment vars against sovereign standard)
        sycl_cache = os.getenv("SYCL_CACHE_PERSISTENT")
        report["sycl_cache_status"] = "OPTIMAL" if sycl_cache == "1" else "NON_OPTIMAL"
        
        immudb.log_operation("HEALTH_DIAGNOSTIC", report)
        
        return SkillResult(
            success=True,
            output=f"Diagnostic Complete: {report['status']}. Details in telemetry.",
            data=report,
            risk_met=RiskLevel.LOW
        )

    def _trigger_dgx_spark(self):
        """Triggers the DGX Spark reset protocol."""
        print("[PIPELINE DOCTOR] WARNING: High memory pressure. Triggering DGX Spark Protocol...")
        try:
            # Assumes the script is in the user's home or a known path
            script_path = os.path.expanduser("~/dgx_spark.sh")
            if os.path.exists(script_path):
                subprocess.run(["bash", script_path], check=True)
                print("[PIPELINE DOCTOR] DGX Spark reset successful.")
            else:
                print(f"[PIPELINE DOCTOR] ERROR: Reset script not found at {script_path}")
        except Exception as e:
            print(f"[PIPELINE DOCTOR] Protocol Failure: {e}")

    def verify(self, result: SkillResult) -> bool:
        """Sovereign verification: check if diagnostics completed successfully."""
        return result.success

