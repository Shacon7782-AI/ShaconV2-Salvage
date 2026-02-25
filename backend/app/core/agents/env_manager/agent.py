import os
import socket
import psutil
import subprocess
from typing import Dict, Any, List
from app.agents.base import GovernedAgent
from app.telemetry import RiskLevel, Blackboard
from app.telemetry.hitl_gate import HITLGate
from app.telemetry.sandbox import SecureSandbox, SandboxException
class EnvironmentManager(GovernedAgent):
    """
    Sovereign Environment Manager (Level 9 Autonomy).
    Monitors infrastructure and executes guarded terminal commands via HITL.
    """
    def __init__(self):
        super().__init__(agent_id="EnvManagerAgent", risk_level=RiskLevel.HIGH)
        self.monitored_ports = [8000, 3000] # Backend and Frontend
        self.critical_files = [".shacon_memory/sovereign.index", "antigravity.db"]
        self.blackboard = Blackboard()
        self.hitl_gate = HITLGate()
        self.allowed_dirs = [os.path.abspath(os.path.join(os.getcwd(), "frontend")), os.path.abspath(os.path.join(os.getcwd(), "backend"))]
        self.blocked_commands = ["rm -rf", "mkfs", "dd ", "chmod -R", "chown -R", "wget ", "curl ", "nc ", "ncat "]

    def audit_environment(self) -> Dict[str, Any]:
        """
        Performs a full infrastructure health check.
        """
        health_report = {
            "ports": self._check_ports(),
            "storage": self._check_critical_files(),
            "resources": self._check_system_resources(),
            "status": "HEALTHY"
        }
        
        if any(not p["up"] for p in health_report["ports"]) or any(not f["exists"] for f in health_report["storage"]):
            health_report["status"] = "DEGRADED"
            
        return health_report

    async def execute_command(self, command: str, target_dir: str = "frontend") -> str:
        """
        Executes a shell command after passing Level 9 HITL authorization.
        """
        print(f"[{self.agent_id}] Evaluating environment mutation: {command}")
        
        # 1. Directory Restriction Check (A+ Security Standard)
        safe_path = os.path.abspath(os.path.join(os.getcwd(), target_dir))
        
        is_safe = False
        for allowed in self.allowed_dirs:
            try:
                if os.path.commonpath([safe_path, allowed]) == allowed:
                    is_safe = True
                    break
            except ValueError:
                pass
                
        if not is_safe:
            return "Error: Execution denied. Target directory outside safe hierarchical bounds."
            
        # 1b. Command Blocklist (A+ Security Standard)
        cmd_lower = command.lower()
        if any(blocked in cmd_lower for blocked in self.blocked_commands):
            return "Error: Execution denied. Command contains blacklisted operations."
            
        # 2. Level 9 HITL Gate
        print(f"[{self.agent_id}] ⚠️ HITL GATE TRIGGERED: Halting for authorization.")
        approval_request = {
            "action": f"Execute Subprocess in {target_dir}",
            "details": f"Command: {command}\nThe system requested this environment mutation."
        }
        
        is_approved = await self.hitl_gate.request_approval(approval_request)
        if not is_approved:
            self.blackboard.post_finding(self.agent_id, f"Execution aborted by Human for: {command}", "env_ops")
            return "Execution aborted by Human Supervisor."
            
        # 3. Execution (Fortified with Smart Governance Sandbox)
        print(f"[{self.agent_id}] Authorization granted. Spawning smart secure sandbox. Executing: {command}")
        
        sandbox = SecureSandbox()
        
        try:
            result = sandbox.run_command(command, safe_path)
            
            output = result.stdout if result.returncode == 0 else result.stderr
            status = "Success" if result.returncode == 0 else "Failed"
            
            self.blackboard.post_finding(
                agent_name=self.agent_id,
                content=f"Command executed in Smart Sandbox: {command}. Status: {status}.",
                related_mission_id="env_ops"
            )
            return output
        except SandboxException as se:
            msg = f"SMART SANDBOX BREACH PREVENTED: Process killed. Reason: {se}"
            self.blackboard.post_finding(self.agent_id, msg, "env_ops")
            return msg
        except Exception as e:
            return f"Sandbox Subprocess Error: {e}"

    def _check_ports(self) -> List[Dict[str, Any]]:
        results = []
        for port in self.monitored_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                is_up = s.connect_ex(('127.0.0.1', port)) == 0
                results.append({"port": port, "up": is_up})
        return results

    def _check_critical_files(self) -> List[Dict[str, Any]]:
        results = []
        for file_path in self.critical_files:
            results.append({"file": file_path, "exists": os.path.exists(file_path)})
        return results

    def _check_system_resources(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_free_gb": psutil.disk_usage('/').free / (1024**3)
        }
