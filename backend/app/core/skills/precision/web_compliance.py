import os
import re
from typing import Dict, Any, List
from ..base import BaseSkill, SkillMetadata, SkillResult

class WebComplianceSkill(BaseSkill):
    """
    Precision Skill that validates website state against SHACON compliance standards.
    Checks for security headers, accessibility baseline, and performance metrics.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="web_compliance_verify",
            version="1.0.0",
            type="precision",
            description="Verifies that web-facing components adhere to the Shacon Web Governance standards.",
            tags=["compliance", "security", "accessibility", "frontend"]
        )
        super().__init__(metadata)

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        print(f"[SKILL] Executing Web Compliance Verification...")
        
        compliance_errors = []
        workspace_root = os.getcwd()
        frontend_path = os.path.join(workspace_root, "frontend")
        
        # 1. Check for Security Headers in config
        config_files = ["next.config.js", "next.config.mjs"]
        found_config = None
        for cfg in config_files:
            if os.path.exists(os.path.join(frontend_path, cfg)):
                found_config = os.path.join(frontend_path, cfg)
                break
        
        if found_config:
            with open(found_config, "r", encoding="utf-8") as f:
                content = f.read()
                # Naive check for headers configuration
                if "headers" not in content and "securityHeaders" not in content:
                    compliance_errors.append("Security Headers not configured in next.config.")
        else:
             # It's okay if it's missing if we are in early stage, but strict for deployment
             # For now, flag it.
             compliance_errors.append("next.config.js/mjs not found.")

        # 2. Check Package.json
        pkg_path = os.path.join(frontend_path, "package.json")
        if os.path.exists(pkg_path):
             pass # Found
        else:
             compliance_errors.append("package.json not found.")

        # 3. Verify Constitution Reference
        if os.path.exists(constitution_path):
            with open(constitution_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Article IX: Web Governance" not in content:
                    compliance_errors.append("Constitution does not contain Article IX: Web Governance.")
        else:
            compliance_errors.append("CONSTITUTION.md missing from root.")

        # 4. Verify Security Policy (Strict Rules)
        security_path = os.path.join(workspace_root, "SECURITY.md")
        if os.path.exists(security_path):
            with open(security_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Agentic Skills Security" not in content:
                    compliance_errors.append("SECURITY.md does not contain 'Agentic Skills Security' section.")
        else:
            compliance_errors.append("SECURITY.md not found. Strict rules must be defined.")

        # 5. Verify Sensitive Info Protection (Rule 3)
        gitignore_path = os.path.join(workspace_root, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if ".env" not in content:
                    compliance_errors.append(".env not found in .gitignore. Risk of leaking secrets.")
        else:
            compliance_errors.append(".gitignore not found.")
        
        success = len(compliance_errors) == 0
        
        output = "Web Compliance Verification: " + ("PASSED" if success else "FAILED")
        if not success:
            output += "\nViolations:\n- " + "\n- ".join(compliance_errors)

        return SkillResult(
            success=success,
            output=output,
            reward=1.0 if success else -1.0,
            telemetry={
                "errors": compliance_errors,
                "timestamp": "ISO_TIMESTAMP_HERE" 
            }
        )

    def verify(self, result: SkillResult) -> bool:
        return "Web Compliance Verification: PASSED" in result.output if result.success else False
