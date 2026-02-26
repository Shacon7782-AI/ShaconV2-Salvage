# Governance: Human-Only Modification Lock (COMPLETE SYSTEM LOCK)

To ensure the integrity and sovereignty of the Shacon V2 system, all critical logic associated with the current stable build (including Swarm, Groq, and Blackboard architectures) is strictly restricted from AI-driven modification.

## 🛑 Protected Directories & Files (LOCKED)

The following paths are under permanent lock. AI agents must NOT attempt to modify these without explicit human override for each specific task.

| Category | Path | Reason for Lock |
| :--- | :--- | :--- |
| **Swarm Logic** | `backend/app/core/agents/` | Core swarm orchestration and agent personas |
| **Blackboard** | `backend/app/core/knowledge_graph.py` | Primary research blackboard/graph logic |
| **Intelligence**| `backend/app/core/llm_router.py` | Groq routing and multi-tier LLM logic |
| **Communication**| `frontend/src/lib/` | API bridge and Intent Engine logic |
| **Restored Data**| `backend/research/`, `backend/research_artifacts/` | Intelligence gathered during the development sprint |
| **Infrastructure**| `docker-compose.yml`, `Dockerfile`, root `package.json` | Environment and dependency definitions |
| **Policy** | `governance/`, `CONSTITUTION.md`, `PRD.md` | Core system rules and product identity |
| **Security** | `backend/security/` | Authentication and encryption protocols |

## 🛠️ Human-Only Modification Protocol

1. **AI Reporting**: The AI agent must explain WHY a change is needed to a locked section.
2. **Explicit Consent**: The human user must provide a specific confirmation (e.g., "UNLOCK VERSION [X.X]").
3. **One-Time Access**: Access is granted only for the duration of the approved modification.
4. **Audit**: all modifications to these paths are recorded in `sentinel_audit.py` for periodic human review.

> [!IMPORTANT]
> This lock protects the "hours and credits" invested in achieving this stable state. 
> Bypassing these restrictions will trigger a Tier-1 compliance alert.
