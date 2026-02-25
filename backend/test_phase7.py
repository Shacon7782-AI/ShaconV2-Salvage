import asyncio
import os
import sys
import json
import requests

# Add current dir to path
sys.path.append(os.getcwd())

from app.core.llm_router import SwarmLLMRouter

def test_router_tiers():
    print("\n--- Testing Economic Waterfall Router Tiers ---")
    
    # We test the routing logic by checking the model response/type if possible
    # or at least verifying it returns a valid LLM instance.
    
    tiers = ["LOW", "MED", "HIGH"]
    for tier in tiers:
        print(f"[TEST] Requesting {tier} complexity LLM...")
        llm = SwarmLLMRouter.get_optimal_llm(complexity=tier)
        if llm:
            print(f"[SUCCESS] {tier} Tier returned LLM type: {type(llm).__name__}")
        else:
            print(f"[FAIL] {tier} Tier failed to return an LLM.")

async def test_dashboard_api():
    print("\n--- Testing Dashboard API Endpoints ---")
    base_url = "http://localhost:8000"
    endpoints = ["/api/dashboard/graph", "/api/dashboard/telemetry", "/api/dashboard/memory", "/api/health"]
    
    for endpoint in endpoints:
        try:
            print(f"[TEST] Fetching {endpoint}...")
            res = requests.get(f"{base_url}{endpoint}")
            if res.status_code == 200:
                data = res.json()
                print(f"[SUCCESS] {endpoint} returned valid JSON. Keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
            else:
                print(f"[FAIL] {endpoint} returned status {res.status_code}")
        except Exception as e:
            print(f"[FAIL] {endpoint} connection failed: {e}. (Ensure backend is running)")

async def main():
    test_router_tiers()
    await test_dashboard_api()

if __name__ == "__main__":
    asyncio.run(main())
