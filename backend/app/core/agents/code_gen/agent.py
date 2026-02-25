#!/usr/bin/env python3
"""
Code Gen Agent — backend/app/agents/code_gen/agent.py
Generates production-ready scaffolding from named templates.
"""
import re
from pathlib import Path
from datetime import datetime, timezone
from string import Template

# ─── Template Definitions ─────────────────────────────────────────────────────
TEMPLATES = {
    "fastapi_endpoint": Template('''\
from fastapi import APIRouter, Depends
from typing import Any

router = APIRouter(prefix="/$path", tags=["$tag"])


@router.get("/")
async def list_$resource() -> list[Any]:
    """List all $resource records."""
    return []


@router.post("/")
async def create_$resource() -> dict:
    """Create a new $resource record."""
    return {"status": "created"}


@router.get("/{item_id}")
async def get_$resource(item_id: int) -> dict:
    """Get a single $resource by ID."""
    return {"id": item_id}


@router.delete("/{item_id}")
async def delete_$resource(item_id: int) -> dict:
    """Delete a $resource by ID."""
    return {"status": "deleted", "id": item_id}
'''),

    "react_component": Template('''\
import React, { useState } from "react"

interface ${Name}Props {
  title?: string
  className?: string
}

export default function $Name({ title = "$Name", className = "" }: ${Name}Props) {
  const [active, setActive] = useState(false)

  return (
    <div className={`$css_class $${className}`} onClick={() => setActive(!active)}>
      <h2>{title}</h2>
      {active && <p>$Name is active</p>}
    </div>
  )
}
'''),

    "python_class": Template('''\
#!/usr/bin/env python3
"""$module_doc"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class $Name:
    """$class_doc"""
    name: str = "$Name"
    config: dict = field(default_factory=dict)

    def run(self, payload: dict | None = None) -> dict:
        """Execute the primary logic of $Name."""
        raise NotImplementedError("Subclasses must implement run()")

    def health_check(self) -> dict:
        return {"status": "ok", "class": self.__class__.__name__}

    def __repr__(self) -> str:
        return f"$Name(name={self.name!r})"
'''),

    "pydantic_schema": Template('''\
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ${Name}Base(BaseModel):
    name: str = Field(..., description="Name of the $resource")


class ${Name}Create(${Name}Base):
    pass


class ${Name}Update(${Name}Base):
    name: Optional[str] = None


class $Name(${Name}Base):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
'''),
}


class CodeGenAgent:
    """
    Generates boilerplate source code from named templates with parameter substitution.
    """

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self._log: list[dict] = []

    def list_templates(self) -> list:
        return list(TEMPLATES.keys())

    def generate(self, template_name: str, params: dict, filename: str) -> str:
        """
        Generate a file from a template.

        Args:
            template_name: Key from TEMPLATES dict.
            params: Substitution variables for the template.
            filename: Output filename (relative to output_dir).

        Returns:
            Absolute path of the generated file.
        """
        if template_name not in TEMPLATES:
            raise ValueError(
                f"Unknown template '{template_name}'. Available: {self.list_templates()}"
            )

        # Safe substitution — leaves unknown $vars intact
        content = TEMPLATES[template_name].safe_substitute(params)

        out_path = self.output_dir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")

        entry = {
            "template": template_name,
            "output": str(out_path),
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._log.append(entry)
        print(f"[CodeGenAgent] ✅ Generated: {out_path}")
        return str(out_path)

    def batch(self, specs: list[dict]) -> list[str]:
        """
        Generate multiple files from a list of spec dicts.
        Each spec must have: template, params, filename.
        """
        results = []
        for spec in specs:
            path = self.generate(spec["template"], spec.get("params", {}), spec["filename"])
            results.append(path)
        return results

    def generation_log(self) -> list[dict]:
        return self._log


if __name__ == "__main__":
    print("[CodeGenAgent] Available templates:")
    agent = CodeGenAgent(output_dir="/tmp/codegen_test")
    for t in agent.list_templates():
        print(f"  - {t}")
