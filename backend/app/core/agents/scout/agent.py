import subprocess
import json
from typing import Dict, Any
from app.core.llm_router import SwarmLLMRouter
from langchain_core.prompts import ChatPromptTemplate
from app.core.telemetry import Blackboard
from app.core.agents.base import GovernedAgent, RiskLevel
from app.core.memory.vector_store import SovereignMemory
from sqlalchemy import text
from app.db.schemas.session import SessionLocal
import os

class ScoutAgent(GovernedAgent):
    """
    The Scout Agent is responsible for monitoring environment drift, 
    understanding file changes semantically, generating commit logs, 
    and posting insights to the Sovereign Blackboard.
    """
    def __init__(self, mock: bool = False):
        super().__init__(agent_id="Scout", risk_level=RiskLevel.LOW)
        self.blackboard = Blackboard()
        self.sovereign_memory = SovereignMemory()
        self.mock = mock
        
        # We need a structured LLM to guarantee JSON output
        self.structured_llm = SwarmLLMRouter.get_optimal_llm(structured_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "A very concise, 1-sentence technical summary of what changed."},
                "commit_message": {"type": "string", "description": "A short, professional git commit message."}
            },
            "required": ["summary", "commit_message"]
        })
        
        if not self.structured_llm:
            print("[SCOUT] WARNING: No API Keys available. Defaulting to MOCK MODE.")
            self.mock = True

    def analyze_environment(self) -> Dict[str, Any]:
        """
        Performs a full system health check and returns a status report.
        Posts anomalies to the Blackboard.
        """
        print("[SCOUT] Initiating full environmental analysis...")
        report = {
            "status": "Nominal",
            "checks": []
        }

        # 1. Check Dropzone
        dropzone_path = "backend/data_dropzone"
        if os.path.exists(dropzone_path):
            report["checks"].append({"name": "Dropzone", "status": "OK"})
        else:
            msg = "CRITICAL: Dropzone directory missing!"
            print(f"[SCOUT] {msg}")
            self.blackboard.post_insight("Scout", msg)
            report["status"] = "Degraded"
            report["checks"].append({"name": "Dropzone", "status": "MISSING"})

        # 2. Check Database Connection
        db_status = self._check_db_health()
        report["checks"].append({"name": "Database", "status": db_status})
        if db_status != "OK":
            msg = f"WARNING: Database connection {db_status.lower()}."
            self.blackboard.post_insight("Scout", msg)
            report["status"] = "Degraded"

        # 3. Check Git Drift (Semantic)
        drift = self._get_git_diff()
        if drift.strip():
            report["checks"].append({"name": "Git Drift", "status": "STALE"})
            # We don't post insight here as run_diff_analysis handles it
        else:
            report["checks"].append({"name": "Git Drift", "status": "SYNCHRONIZED"})

        report["summary"] = f"System {report['status']}. {len(report['checks'])} checks performed."
        return report

    def _check_db_health(self) -> str:
        """Verifies pgvector database connectivity."""
        db = SessionLocal()
        try:
            # Simple query to verify connection
            db.execute(text("SELECT 1"))
            return "OK"
        except Exception as e:
            print(f"[SCOUT] DB Health Check failed: {e}")
            return "FAIL"
        finally:
            db.close()

    def run_diff_analysis(self) -> bool:
        """
        Runs `git diff HEAD`, analyzes it, and commits if there are changes.
        """
        print("[SCOUT] Scanning environment for drift...")
        diff = self._get_git_diff()
        
        if not diff.strip():
            print("[SCOUT] No significant drift detected. Environment Stable.")
            return False
            
        if self.mock:
            print("[SCOUT] MOCK MODE: Detected changes, taking no action.")
            return False
            
        print("[SCOUT] Drift detected. Generating semantic commit analysis...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Scout Agent of the Shacon Workspace. Your job is to analyze the git diff of recent codebase changes, provide a very concise, 1-sentence technical summary of the changes, and generate a short commit message (under 50 chars if possible). Return strictly a JSON object with 'summary' and 'commit_message' keys."),
            ("human", "Here is the raw git diff:\n\n{diff}")
        ])
        
        try:
            # Prevent excessive token usage by truncating huge diffs
            truncated_diff = diff[:6000]
            if len(diff) > 6000:
                truncated_diff += "\n...[DIFF TRUNCATED]..."
                
            chain = prompt | self.structured_llm
            result = chain.invoke({"diff": truncated_diff})
            
            summary = result.get("summary", "Codebase drifted. Routine automated sync.")
            commit_msg = result.get("commit_message", "Sovereign Stabilization: Automated file sync")
            
            # 1. Post to Blackboard
            print(f"[SCOUT] Insight Generation Complete: {summary}")
            if hasattr(self.blackboard, 'post_insight'):
                self.blackboard.post_insight("Scout", summary)
            else:
                self.blackboard.post_finding("Scout", summary)
                
            # 2. NEW: Autonomous Sovereign Memory Codebase History
            try:
                memory_payload = f"Codebase Evolution (Scout): {summary} | Commit string: {commit_msg}"
                print(f"[SCOUT] Autonomous Memory Commit: Recording codebase state.")
                self.sovereign_memory.commit_to_memory(memory_payload, {"type": "codebase_evolution", "diff_snippet": truncated_diff[:500]})
            except Exception as e:
                print(f"[SCOUT] Memory commit failed: {e}")
            
            # 3. Execute Commit via the Auto-Commit script
            return self._execute_commit(commit_msg)
            
        except Exception as e:
            print(f"[SCOUT] Error generating insight: {e}")
            # Fallback
            return self._execute_commit("Sovereign Stabilization: Routine automated sync (Fallback)")

    def _get_git_diff(self) -> str:
        try:
            # We want to see differences of tracked files, maybe also untracked?
            # 'git status -s' shows overall. 'git diff HEAD' shows actual line changes.
            result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, check=False)
            return result.stdout
        except Exception as e:
            print(f"[SCOUT] Git diff failed: {e}")
            return ""

    def _execute_commit(self, message: str) -> bool:
        try:
            print(f"[SCOUT] Dispatching auto_commit.py with message: '{message}'")
            # We run the existing script so we don't duplicate the sovereign list of tracked files
            res = subprocess.run(["python", "scripts/auto_commit.py", message], capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[SCOUT] Auto-commit successful.")
                return True
            else:
                print(f"[SCOUT] Auto-commit yielded non-zero exit: {res.stdout} | {res.stderr}")
                return False
        except Exception as e:
            print(f"[SCOUT] Failed to execute auto_commit: {e}")
            return False

if __name__ == "__main__":
    scout = ScoutAgent()
    scout.run_diff_analysis()
