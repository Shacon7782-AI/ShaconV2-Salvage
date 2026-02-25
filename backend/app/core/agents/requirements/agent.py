#!/usr/bin/env python3
"""
Requirements Agent — backend/app/agents/requirements/agent.py
Audits Python dependency manifests and scans source imports.
"""
import ast
import sys
import importlib.util
from pathlib import Path


class RequirementsAgent:
    """
    Scans requirements.txt files in the project and verifies declared
    dependencies are present and importable.
    """

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.manifests = list(self.root.rglob("requirements*.txt"))

    def list_manifests(self) -> list:
        return [str(m.relative_to(self.root)) for m in self.manifests]

    def read(self, manifest_path: str) -> list:
        path = self.root / manifest_path
        if not path.exists():
            return []
        pkgs = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-r"):
                continue
            # Strip version specifiers: pkg>=1.0 → pkg, pkg==2.0 → pkg
            name = line.split(">=")[0].split("==")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip()
            pkgs.append(name)
        return pkgs

    def check_importable(self, package_name: str) -> bool:
        """Check if a package is importable in the current Python environment."""
        # Normalize: google-cloud-storage → google.cloud.storage, python-dotenv → dotenv
        normalized = package_name.replace("-", "_").lower()
        for name in [normalized, package_name.replace("-", ".").lower()]:
            if importlib.util.find_spec(name) is not None:
                return True
        return False

    def scan_imports(self, src_dir: str = None) -> set:
        """
        Scan all .py files under src_dir and collect top-level import names.
        """
        imports = set()
        target = self.root / (src_dir or "backend")
        for py_file in target.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split(".")[0])
            except Exception:
                continue
        return imports

    def audit(self) -> dict:
        """Returns full audit with importability status per package."""
        result = {}
        for m in self.manifests:
            pkgs = self.read(str(m.relative_to(self.root)))
            entries = []
            for pkg in pkgs:
                importable = self.check_importable(pkg)
                entries.append({"package": pkg, "importable": importable})
            result[str(m.relative_to(self.root))] = {
                "total": len(pkgs),
                "importable": sum(1 for e in entries if e["importable"]),
                "missing": [e["package"] for e in entries if not e["importable"]],
            }
        return result

    def report(self) -> None:
        print(f"[RequirementsAgent] Auditing {len(self.manifests)} manifest(s)...\n")
        for manifest, data in self.audit().items():
            status = "✅" if not data["missing"] else "⚠️ "
            print(f"  {status} {manifest}: {data['importable']}/{data['total']} importable")
            if data["missing"]:
                print(f"     Missing: {', '.join(data['missing'])}")
        # Cross-check with actual imports
        imports = self.scan_imports()
        print(f"\n[RequirementsAgent] Unique top-level imports found in backend: {len(imports)}")


if __name__ == "__main__":
    agent = RequirementsAgent(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
    agent.report()
