import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.skills.precision.cloud_researcher import CloudResearcherSkill

async def test_full_pipeline():
    print("=== Testing Full Ingestion & Synthesis Pipeline ===")
    
    skill = CloudResearcherSkill()
    
    # Simple query that should yield results
    inputs = {
        "query": "Impact of Llama 3.3 on agentic workflows",
        "mission_id": "test-audit-001"
    }
    
    print(f"Executing Researcher Skill for: {inputs['query']}")
    result = await skill.execute(inputs)
    
    if result.success:
        print("\n--- SYNTHESIS SUCCESS ---")
        print(f"Output Preview: {result.output[:300]}...")
        print(f"Telemetry: {result.telemetry}")
    else:
        print(f"\n--- SYNTHESIS FAILED: {result.output} ---")

    # Verify audit log again
    from verify_sovereign_audit import verify_audit_chain
    verify_audit_chain()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
