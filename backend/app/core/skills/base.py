import abc
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class SkillMetadata(BaseModel):
    name: str
    version: str
    type: str  # precision, logic, generic
    description: str
    tags: List[str]

class SkillResult(BaseModel):
    success: bool
    output: Any
    reward: float = 0.0
    telemetry: Dict[str, Any] = {}

class BaseSkill(abc.ABC):
    """
    Abstract Base Class for all Shacon Skills.
    Enforces the 'Precision Layer' standards.
    """
    def __init__(self, metadata: SkillMetadata):
        self.skill_metadata = metadata

    @abc.abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """Main execution logic for the skill."""
        pass

    @abc.abstractmethod
    def verify(self, result: SkillResult) -> bool:
        """Formal verification of the skill's outcome."""
        pass

class SkillRegistry:
    """
    Central registry for discovering and calling agent skills.
    Integrates with MCP for system-wide discovery.
    """
    _instance = None
    _skills: Dict[str, BaseSkill] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, skill: BaseSkill):
        print(f"[REGISTRY] Registering skill: {skill.skill_metadata.name} v{skill.skill_metadata.version}")
        self._skills[skill.skill_metadata.name] = skill

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        return self._skills.get(name)

    def list_skills(self) -> List[SkillMetadata]:
        return [skill.skill_metadata for skill in self._skills.values()]
