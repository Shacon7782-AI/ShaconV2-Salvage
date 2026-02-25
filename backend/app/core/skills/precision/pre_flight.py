import os
import sys
from typing import Dict, Any
from ..base import BaseSkill, SkillMetadata, SkillResult
from ..base import BaseSkill, SkillMetadata, SkillResult

# Dynamic import for hidden .agent directory
import importlib.util
import os

def load_sandbox_gate():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
    gate_path = os.path.join(root_dir, ".agent", "simulations", "armory_gate.py")
    spec = importlib.util.spec_from_file_location("armory_gate", gate_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ArmoryGate

class PreFlightSkill(BaseSkill):
    """
    The 'Armory' gatekeeper skill.
    Simulates a proposed command in the sandbox and verifies safety.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="pre_flight_check",
            version="1.0.0",
            type="simulation",
            description="Verifies a proposed team action or code change in a Docker-based simulation sandbox before execution.",
            tags=["safety", "simulation", "verification"]
        )
        super().__init__(metadata)
        try:
            self.GateClass = load_sandbox_gate()
            self.gate = self.GateClass()
        except Exception as e:
            print(f"[SKILL] Warning: Failed to load ArmoryGate: {e}")
            self.gate = None

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        command = inputs.get("command")
        if not command:
            return SkillResult(success=False, output="Missing command for simulation", reward=-1.0)
            
        print(f"[SKILL] Initiating Pre-Flight Check for: {command}")
        
        # In this implementation phase, we simulate the GATE response if Docker is unavailable
        # or handle real execution if enabled.
        
        try:
            # We assume 'mock_gate' for now if we don't want to force Docker build on every agent call
            # In a real setup, this would call self.gate.run_simulation(command)
            
            sim_res = self.gate.run_simulation(command)
            
            if sim_res["success"]:
                return SkillResult(
                    success=True, 
                    output=f"Simulation Successful. Command validated in isolated container.\nOutput: {sim_res['output'][:500]}", 
                    reward=1.0
                )
            else:
                return SkillResult(
                    success=False, 
                    output=f"SIMULATION FAILED: Safety violation or error detected.\nError: {sim_res['error']}",
                    reward=-2.0
                )
                
        except Exception as e:
            return SkillResult(success=False, output=f"Armory System Error: {str(e)}", reward=-5.0)

    def verify(self, result: SkillResult) -> bool:
        return result.success
