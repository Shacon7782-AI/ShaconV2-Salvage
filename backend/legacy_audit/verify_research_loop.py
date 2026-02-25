import asyncio
import os
from dotenv import load_dotenv

# Set up environment
load_dotenv()

# We need to set some dummy keys if they aren't present just for the instantiation check
# if not os.getenv("GOOGLE_API_KEY"):
#     os.environ["GOOGLE_API_KEY"] = "mock_key"

from app.core.agents.researcher.agent import ResearchAgent
from app.core.telemetry import Blackboard

async def verify():
    print("--- STARTING RESEARCH LOOP VERIFICATION ---")
    
    # 1. Initialize Agent
    print("[STEP 1] Initializing ResearchAgent...")
    try:
        agent = ResearchAgent()
        print("[SUCCESS] ResearchAgent initialized.")
    except Exception as e:
        print(f"[FAIL] ResearchAgent initialization failed: {e}")
        return

    # 2. Test Run (Mocking Search or using real if keys exist)
    print("\n[STEP 2] Running Research Discovery...")
    query = "What is the capital of France?"
    
    try:
        # We'll use a simple query. If APIs fail, the agent should handle it gracefully.
        result = await agent.run(query)
        print(f"[SUCCESS] Research run completed. Source: {result.get('source')}")
    except Exception as e:
        print(f"[FAIL] Research run failed: {e}")

    # 3. Check Blackboard
    print("\n[STEP 3] Verifying Blackboard Posts...")
    blackboard = Blackboard()
    findings = blackboard.get_recent_findings()
    insights = blackboard.get_recent_insights()

    if findings:
        print(f"[SUCCESS] Found {len(findings)} findings on the blackboard.")
        for f in findings:
            print(f"  - {f['agent_id']}: {f['content'][:100]}")
    else:
        print("[FAIL] No findings found on the blackboard.")

    if insights:
        print(f"[SUCCESS] Found {len(insights)} insights on the blackboard.")
    else:
        print("[NOTE] No insights posted yet (usually by Scout).")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify())
