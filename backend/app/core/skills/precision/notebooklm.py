import subprocess
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.app.core.skills.base import BaseSkill, SkillMetadata, SkillResult

class NotebookLMSkill(BaseSkill):
    """
    Bridge skill for Google NotebookLM Browser Automation.
    Allows agents to query complex research notebooks.
    """
    
    def __init__(self):
        metadata = SkillMetadata(
            name="notebooklm_research",
            version="1.0.0",
            type="precision",
            description="Queries Google NotebookLM via browser automation for deep research context.",
            tags=["research", "notebooklm", "automation", "browser"]
        )
        super().__init__(metadata)
        
        # Paths
        self.skill_root = Path(__file__).parent / "notebooklm"
        self.runner = self.skill_root / "scripts" / "run.py"
        self.ask_script = "ask_question.py"
        self.manager_script = "notebook_manager.py"
        self.auth_script = "auth_manager.py"

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        Executes NotebookLM actions based on input 'action'.
        Actions: query, add_notebook, list_notebooks, check_auth
        """
        action = inputs.get("action", "query")
        
        if action == "query":
            return self._query(inputs)
        elif action == "add_notebook":
            return self._add_notebook(inputs)
        elif action == "list_notebooks":
            return self._list_notebooks()
        elif action == "check_auth":
            return self._check_auth()
        else:
            return SkillResult(
                success=False,
                output=f"Unknown action: {action}",
                telemetry={"action": action}
            )

    def _query(self, inputs: Dict[str, Any]) -> SkillResult:
        question = inputs.get("question")
        notebook_id = inputs.get("notebook_id")
        
        if not question:
            return SkillResult(success=False, output="Missing 'question' input")
        
        cmd = [
            "python", str(self.runner), self.ask_script,
            "--question", question
        ]
        
        if notebook_id:
            cmd.extend(["--notebook-id", notebook_id])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                # Extract the actual answer from the output (it has headers/footers)
                # For now, return full output as the script handles formatting
                return SkillResult(
                    success=True,
                    output=result.stdout,
                    telemetry={"notebook_id": notebook_id}
                )
            else:
                return SkillResult(
                    success=False,
                    output=f"NotebookLM Error: {result.stderr or result.stdout}",
                    telemetry={"exit_code": result.returncode}
                )
        except Exception as e:
            return SkillResult(success=False, output=str(e))

    def _add_notebook(self, inputs: Dict[str, Any]) -> SkillResult:
        url = inputs.get("url")
        name = inputs.get("name")
        description = inputs.get("description", "")
        topics = inputs.get("topics", [])
        
        if not url or not name:
            return SkillResult(success=False, output="Missing 'url' or 'name'")
            
        cmd = [
            "python", str(self.runner), self.manager_script, "add",
            "--url", url,
            "--name", name,
            "--description", description,
            "--topics", ",".join(topics) if isinstance(topics, list) else topics
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return SkillResult(success=result.returncode == 0, output=result.stdout)
        except Exception as e:
            return SkillResult(success=False, output=str(e))

    def _list_notebooks(self) -> SkillResult:
        cmd = ["python", str(self.runner), self.manager_script, "list"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return SkillResult(success=result.returncode == 0, output=result.stdout)
        except Exception as e:
            return SkillResult(success=False, output=str(e))

    def _check_auth(self) -> SkillResult:
        cmd = ["python", str(self.runner), self.auth_script, "status"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return SkillResult(success=result.returncode == 0, output=result.stdout)
        except Exception as e:
            return SkillResult(success=False, output=str(e))

    def verify(self, result: SkillResult) -> bool:
        """Verify the quality of the research output."""
        if not result.success:
            return False
        # Basic check for actual content
        return len(str(result.output)) > 50
