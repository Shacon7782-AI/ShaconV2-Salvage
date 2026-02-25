from backend.app.core.skills.base import SkillRegistry
from backend.app.core.skills.precision.system_integrity import SystemIntegritySkill
from backend.app.core.skills.precision.deep_research import DeepResearchSkill
from backend.app.core.skills.precision.recall import RecallSkill
from backend.app.core.skills.precision.discovery import DiscoverySkill
from backend.app.core.skills.precision.autonomous_loop import AutonomousVerificationLoop
from backend.app.core.skills.precision.optimization import OptimizationSkill
from backend.app.core.skills.precision.env_manager import EnvironmentManagerSkill
from backend.app.core.skills.precision.credits import CreditSkill
from backend.app.core.skills.precision.pre_flight import PreFlightSkill
from backend.app.core.skills.precision.system_integrity import SystemIntegritySkill
from backend.app.core.skills.precision.deep_research import DeepResearchSkill
from backend.app.core.skills.precision.self_heal import SelfHealSkill
from backend.app.core.skills.precision.sovereign_handshake import SovereignHandshakeSkill
from backend.app.core.skills.precision.interviewer import ConsultativeInterviewSkill
from backend.app.core.skills.precision.visual_builder import VisualBuilderSkill
from backend.app.core.skills.precision.semantic_memory import SemanticMemorySkill
from backend.app.core.skills.precision.notebooklm import NotebookLMSkill

def initialize_skill_registry():
    """
    Bootstraps the Skill Registry with all precision and logic skills.
    This should be called during backend startup.
    """
    registry = SkillRegistry()
    
    # Register Precision Skills
    registry.register(SystemIntegritySkill())
    registry.register(DeepResearchSkill())
    registry.register(SelfHealSkill())
    registry.register(SovereignHandshakeSkill())
    registry.register(PreFlightSkill())
    registry.register(RecallSkill())
    registry.register(DiscoverySkill())
    registry.register(AutonomousVerificationLoop())
    registry.register(EnvironmentManagerSkill())
    registry.register(OptimizationSkill()) 
    registry.register(CreditSkill())
    registry.register(ConsultativeInterviewSkill())
    registry.register(VisualBuilderSkill())
    registry.register(SemanticMemorySkill())
    registry.register(NotebookLMSkill())
    
    # Registration for future skills goes here...
    # registry.register(DatabaseOptimizingSkill())
    
    print(f"[BOOT] Skill Registry initialized with {len(registry.list_skills())} skills.")

if __name__ == "__main__":
    initialize_skill_registry()
