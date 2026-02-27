from app.core.skills.base import SkillRegistry
from app.core.skills.precision.system_integrity import SystemIntegritySkill
from app.core.skills.precision.deep_research import DeepResearchSkill
from app.core.skills.precision.recall import RecallSkill
from app.core.skills.precision.discovery import DiscoverySkill
# from app.core.skills.precision.autonomous_loop import AutonomousVerificationLoop
# from app.core.skills.precision.optimization import OptimizationSkill
from app.core.skills.precision.env_manager import EnvironmentManagerSkill
# from app.core.skills.precision.credits import CreditSkill
# from app.core.skills.precision.pre_flight import PreFlightSkill
from app.core.skills.precision.self_heal import SelfHealSkill
# from app.core.skills.precision.sovereign_handshake import SovereignHandshakeSkill
# from app.core.skills.precision.interviewer import ConsultativeInterviewSkill
from app.core.skills.precision.visual_builder import VisualBuilderSkill
from app.core.skills.precision.semantic_memory import SemanticMemorySkill
from app.core.skills.precision.pipeline_doctor import PipelineDoctorSkill


# Global Registry Instance
registry = SkillRegistry()

def initialize_skill_registry():
    """
    Bootstraps the Skill Registry with all precision and logic skills.
    This should be called during backend startup.
    """
    # Register Precision Skills
    registry.register(SystemIntegritySkill())
    registry.register(DeepResearchSkill())
    registry.register(SelfHealSkill())
    # registry.register(SovereignHandshakeSkill())
    # registry.register(PreFlightSkill())
    registry.register(RecallSkill())
    registry.register(DiscoverySkill())
    # registry.register(AutonomousVerificationLoop())
    registry.register(EnvironmentManagerSkill())
    # registry.register(OptimizationSkill()) 
    # registry.register(CreditSkill())
    # registry.register(ConsultativeInterviewSkill())
    registry.register(VisualBuilderSkill())
    registry.register(SemanticMemorySkill())
    registry.register(PipelineDoctorSkill())

    # Registration for future skills goes here...
    # registry.register(DatabaseOptimizingSkill())
    
    print(f"[BOOT] Skill Registry initialized with {len(registry.list_skills())} skills.")

if __name__ == "__main__":
    initialize_skill_registry()
