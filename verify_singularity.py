import asyncio
import os
import sys

# Ensure backend path is in sys.path
backend_path = os.path.join(os.getcwd(), "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.core.memory.vector_store import SovereignMemory
from app.core.agents.orchestrator.agent import Orchestrator
from app.core.skills.base import SkillRegistry
from app.core.triage import SovereignTriage
from app.core.memory.durable_execution import DurableContext

from app.core.skills.boot import initialize_skill_registry

async def verify_singularity():
    print("\n--- [SINGULARITY VERIFICATION START] ---\n")
    
    # Bootstrap the registry
    initialize_skill_registry()

    # 1. Verify XPU Offloading
    print("1. [HARDWARE] Testing Intel XPU (iGPU) Detection...")
    memory = SovereignMemory()
    print(f"   Detected Device: {memory.device}")
    if memory.device == "xpu":
        print("   SUCCESS: Intel Iris Xe Offloading ACTIVE.")
    else:
        print("   NOTE: XPU not detected (standard fallback active).")

    # 2. Verify 16-Phase Triage
    print("\n2. [TRIAGE] Testing 16-Phase Protocol...")
    triage = SovereignTriage()
    intent = "Research the enterprise benchmark report and find efficiency gaps."
    res = await triage.execute_triage(intent)
    print(f"   Triage Result: Complexity={res.complexity}, Risk={res.risk_level.value}")
    
    # Verify Post-Execution Phase
    post_res = await triage.execute_post_execution_triage("VALIDATION_TEST", {"status": "SUCCESS", "output": "Data found."})
    print(f"   Post-Execution Validation: {'SUCCESS' if post_res else 'FAILED'}")

    # 3. Verify Durable Execution & Recovery
    print("\n3. [RESILIENCE] Testing Durable Checkpoint & Recovery...")
    task_id = "SINGULARITY_RECOVERY_TEST_01"
    durable = DurableContext(task_id)
    durable.checkpoint("TEST_STEP", {"payload": "Resilience Pulse"})
    
    print("   Simulating State Loss and Recovery...")
    recovered_state = DurableContext.recover(task_id)
    if recovered_state and recovered_state.get("name") == "TEST_STEP":
        print("   SUCCESS: Durable state reconstrituted from immudb chain.")
    else:
        print("   FAILED: Recovery chain broken.")

    # 4. Verify Pipeline Doctor
    print("\n4. [SELF-HEALING] Verifying Pipeline Doctor Registration...")
    from app.core.skills.precision.pipeline_doctor import PipelineDoctorSkill
    registry = SkillRegistry()
    doctor = registry.get_skill("pipeline_doctor")
    if doctor:
        print("   SUCCESS: Pipeline Doctor is heart-beating in the registry.")
    else:
        print("   FAILED: Pipeline Doctor not found.")

    print("\n--- [SINGULARITY VERIFICATION COMPLETE] ---\n")

if __name__ == "__main__":
    asyncio.run(verify_singularity())
