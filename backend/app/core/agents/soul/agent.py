import subprocess
import os
import asyncio
from typing import Dict, Any
from backend.app.core.llm_router import SwarmLLMRouter
from langchain_core.prompts import ChatPromptTemplate
from backend.app.telemetry import Blackboard, RiskLevel
from backend.app.agents.base import GovernedAgent
from backend.app.core.memory.vector_store import SovereignMemory

class SoulAgent(GovernedAgent):
    """
    The Soul Agent is the Structural Auditor. It autonomously manages the 
    quarantine zone, restores critical assets, and disposes of legacy debt 
    based on systemic context.
    """
    def __init__(self, mock: bool = False):
        super().__init__(agent_id="Soul", risk_level=RiskLevel.CRITICAL)
        self.blackboard = Blackboard()
        self.sovereign_memory = SovereignMemory()
        self.mock = mock
        
        self.structured_llm = None
        try:
            self.structured_llm = SwarmLLMRouter.get_optimal_llm(structured_schema={
                "type": "object",
                "properties": {
                    "audit_summary": {"type": "string", "description": "A summary of the quarantine zone audit."},
                    "safe_to_sweep": {"type": "boolean", "description": "Whether it is safe to permanently delete the quarantined files."}
                },
                "required": ["audit_summary", "safe_to_sweep"]
            })
        except Exception as e:
            print(f"[SOUL] LLM Router failed to initialize structured LLM: {e}")
            self.mock = True
            
        if not self.structured_llm:
            print("[SOUL] WARNING: No API Keys available. Defaulting to MOCK MODE.")
            self.mock = True

    async def run_deep_audit(self):
        """
        Runs the deep audit: checks quarantine, evaluates if sweeping is safe,
        and triggers the zombie sweep.
        """
        print("\n[SOUL] Initiating Deep Structural Audit...")
        
        # Use abs path mostly because daemon might run from elsewhere
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        quarantine_dir = os.path.join(root_dir, ".shacon_quarantine")
        
        # 1. Analyze Quarantine
        if not os.path.exists(quarantine_dir):
            print("[SOUL] Quarantine directory not found. Environment behaves nominally.")
            return

        files = os.listdir(quarantine_dir)
        if not files:
            print("[SOUL] Quarantine is empty. Environment behaves nominally.")
            return

        file_list_str = "\n".join(files[:20]) # Limit to 20
        if len(files) > 20:
            file_list_str += f"\n...and {len(files)-20} more."

        if self.mock:
            if hasattr(self.blackboard, 'post_insight'):
                self.blackboard.post_insight("Soul", f"Mock Audit: Found {len(files)} files in quarantine. Skipping sweep.")
            else:
                self.blackboard.post_finding("Soul", f"Mock Audit: Found {len(files)} files in quarantine. Skipping sweep.")
            return

        print(f"[SOUL] Found {len(files)} items in quarantine. Generating structural assessment...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Soul Agent, the strict structural auditor of the Shacon Workspace. Your job is to review the list of quarantined files and determine if it is safe to permanently purge them (zombie sweep). Usually, if they are just old temp files, python caches, or known bad files, it is safe to sweep. Return strictly a JSON object with 'audit_summary' and 'safe_to_sweep' (boolean)."),
            ("human", f"Quarantined files:\n{file_list_str}")
        ])
        
        try:
            chain = prompt | self.structured_llm
            result = chain.invoke({})
            
            summary = result.get("audit_summary", "Quarantine audit complete. Commencing sweep.")
            safe = result.get("safe_to_sweep", True)
            
            msg = f"Audit complete: {summary} Sweep authorized: {safe}"
            if hasattr(self.blackboard, 'post_insight'):
                self.blackboard.post_insight("Soul", msg)
            else:
                self.blackboard.post_finding("Soul", msg)
                
            # NEW: Autonomous Sovereign Memory Commitment for Danger Patterns
            try:
                memory_payload = f"Soul Agent Quarantine Audit: Found {len(files)} unauthorized or dangerous files. Summary: {summary}. Safe to sweep: {safe}."
                print(f"[SOUL] Autonomous Memory Commit: Recording architectural hazard.")
                file_subset = files[:10] if isinstance(files, list) else []
                self.sovereign_memory.commit_to_memory(memory_payload, {"type": "architectural_hazard", "files": file_subset})
            except Exception as e:
                print(f"[SOUL] Memory commit failed: {e}")
            
            # 2. Trigger zombie_sweep.ps1 if safe
            if safe:
                self._trigger_sweep(root_dir)
                
        except Exception as e:
            print(f"[SOUL] Audit generation failed: {e}")
            if hasattr(self.blackboard, 'post_insight'):
                self.blackboard.post_insight("Soul", "Deep Audit encountered a cognitive error. Falling back to defensive preservation.")
            else:
                self.blackboard.post_finding("Soul", "Deep Audit encountered a cognitive error. Falling back to defensive preservation.")

    def _trigger_sweep(self, cwd: str):
        print("[SOUL] Authorizing execution of zombie_sweep.ps1...")
        try:
            res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts/zombie_sweep.ps1"], cwd=cwd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[SOUL] Zombie sweep executed successfully.")
            else:
                print(f"[SOUL] Zombie sweep yielded non-zero exit: {res.stderr}")
        except Exception as e:
            print(f"[SOUL] Failed to execute zombie sweep: {e}")

async def soul_daemon():
    """Background loop to run the Soul Agent every hour."""
    # Add a slight delay at boot so it doesn't collide with initialization
    await asyncio.sleep(60) 
    
    agent = SoulAgent()
    while True:
        try:
            await agent.run_deep_audit()
        except Exception as e:
            print(f"[SOUL-DAEMON] Error during deep audit: {e}")
            
        # Wait 1 hour between sweeps
        await asyncio.sleep(3600)

if __name__ == "__main__":
    agent = SoulAgent()
    asyncio.run(agent.run_deep_audit())
