import os
import subprocess
import shutil
from typing import Dict, Any, Tuple
from app.core.agents.base import GovernedAgent, RiskLevel
from app.core.telemetry import Blackboard
from app.core.llm_router import SwarmLLMRouter
from app.core.config import settings
from app.core.memory.vector_store import SovereignMemory
class VisualAgent(GovernedAgent):
    """
    The Autonomous Visual Worker (Level 9).
    Drafts React components using internal design system logic, places them into Next.js routes,
    and runs a verification build to ensure it compiles.
    """
    def __init__(self):
        super().__init__(agent_id="VisualAgent", risk_level=RiskLevel.MEDIUM)
        self.blackboard = Blackboard()
        self.sovereign_memory = SovereignMemory()
        
        # Arbitrage Routing
        self.llm = SwarmLLMRouter.get_optimal_llm()
        
    def run(self, prompt: str, target_route: str = None, component_name: str = "GeneratedComponent") -> str:
        """
        Executes the visual generation loop.
        If target_route is provided (e.g., '/app/dashboard/page.tsx'), it creates the full route.
        Otherwise, defaults to a reusable component.
        """
        if not self.llm:
            return "VisualAgent failed: No valid API key provided for LLM engine."
            
        print(f"[{self.agent_id}] Initiating UI Build Loop for: {prompt}")
        
        # 1. Fetch UI/UX Design System and Soverign Memory
        design_system = self._fetch_design_system(prompt)
        past_patterns = ""
        try:
            memories = self.sovereign_memory.recall(prompt, top_k=2)
            if memories:
                past_patterns = "\\n".join([f"- {m['content']}" for m in memories])
        except Exception as e:
            print(f"[{self.agent_id}] Memory recall failed: {e}")
        
        # 2. Instruct the LLM
        self.blackboard.post_finding(
            agent_name=self.agent_id,
            content=f"Drafting UI implementation...",
            related_mission_id="ui_build"
        )
        
        route_instruction = ""
        if target_route:
            route_instruction = f"This code is meant to be a Next.js App Router page located at `{target_route}`. Export it as the default page component."
        else:
            route_instruction = f"This code is a reusable React component named `{component_name}`."
            
        system_instruction = f"""
        You are the VisualAgent for the Shacon Workspace.
        You generate professional Next.js / React (Tailwind) code based on the provided DESIGN SYSTEM.
        Return ONLY valid React code. Do NOT wrap it in markdown block quotes (no ```tsx).
        Your output will be saved directly to a .tsx file.
        
        {route_instruction}
        
        DESIGN SYSTEM:
        {design_system}
        
        KNOWN GOOD PATTERNS & MEMORIES:
        {past_patterns or "None"}
        """
        
        try:
            response = self.llm.invoke(system_instruction + "\\n\\nUser Request: " + prompt)
            code = response.content.replace("```tsx", "").replace("```", "").strip()
            
            # 3. Determine File Path
            frontend_dir = os.path.join(os.getcwd(), "frontend")
            
            if target_route:
                # Strip leading slash if present
                clean_route = target_route.lstrip("/")
                out_file = os.path.join(frontend_dir, clean_route)
            else:
                out_dir = os.path.join(frontend_dir, "components", "generated")
                os.makedirs(out_dir, exist_ok=True)
                out_file = os.path.join(out_dir, f"{component_name}.tsx")
                
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            
            # Backup existing file if it exists (for revert on build fail)
            backup_file = out_file + ".bak"
            if os.path.exists(out_file):
                shutil.copy2(out_file, backup_file)
            
            # Write new code
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(code)
                
            self.blackboard.post_finding(
                agent_name=self.agent_id,
                content=f"Generated React code at {out_file}. Beginning Next.js build verification...",
                related_mission_id="ui_build"
            )
            
            # 4. Verify Build Compilation
            # Next.js compiles happen in the frontend directory
            build_success, build_log = self._verify_build(frontend_dir)
            
            if build_success:
                # Cleanup backup
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                    
                msg = f"Component generated and verified successfully at {out_file}."
                self.blackboard.post_finding(self.agent_id, msg, "ui_build")
                
                # 5. NEW: Auto-commit to permanent Sovereign Memory
                try:
                    summary = f"VisualAgent successfully built Next.js component '{component_name}' for target route '{target_route}'. Code pattern: {code[:400]}..."
                    print(f"[{self.agent_id}] Autonomous Memory Commit: Saving verified UI pattern.")
                    self.sovereign_memory.commit_to_memory(summary, {"type": "visual_pattern"})
                except Exception as e:
                    print(f"[{self.agent_id}] Memory commit failed: {e}")
                    
                return msg
            else:
                # Revert
                if os.path.exists(backup_file):
                    shutil.move(backup_file, out_file)
                else:
                    os.remove(out_file) # Delete the broken file
                    
                error_msg = f"Build failed after generating UI. Reverted changes. Build error snippet: {build_log}"
                self.blackboard.post_finding(self.agent_id, error_msg, "ui_build", risk_level=RiskLevel.HIGH)
                return error_msg
            
        except Exception as e:
            return f"Visual Agent failed: {e}"
            
    def _verify_build(self, frontend_dir: str) -> Tuple[bool, str]:
        """Runs the Next.js compiler to ensure the generated code doesn't break the app."""
        try:
            print(f"[{self.agent_id}] Running 'npm run build' verification...")
            # We use next build to check type errors and compilation
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True, 
                text=True,
                check=False # We handle the error manually
            )
            
            if result.returncode == 0:
                print(f"[{self.agent_id}] Verification passed.")
                return True, ""
            else:
                print(f"[{self.agent_id}] Verification FAILED!")
                # Get the last 1500 chars of the error log for the LLM context
                error_snippet = (result.stderr + result.stdout)[-1500:]
                return False, error_snippet
                
        except Exception as e:
            return False, str(e)

    def _fetch_design_system(self, query: str) -> str:
        print(f"[{self.agent_id}] Retrieving UI/UX logic for: {query}")
        try:
            script_path = os.path.join(os.getcwd(), ".agent", "skills", "ui-ux-pro-max", "scripts", "search.py")
            if not os.path.exists(script_path):
                return "Default Design System: Use Tailwind CSS, clean layouts, and professional SaaS patterns."
                
            result = subprocess.run(
                ["python", script_path, query, "--design-system"],
                capture_output=True, text=True, check=True
            )
            return result.stdout
        except Exception as e:
            print(f"[{self.agent_id}] UI/UX Pro Max lookup failed: {e}")
            return "Default Design System: Use Tailwind CSS, clean layouts, and professional aesthetic."
