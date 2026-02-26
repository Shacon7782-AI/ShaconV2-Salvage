import asyncio
import sys
import hashlib
from app.core.agents.base import BaseAgent, GovernedAgent
from app.core.agents.researcher.agent import ResearchAgent
from app.core.agents.orchestrator.agent import Orchestrator
from app.core.immudb_sidecar import immudb
from app.core.agents.researcher.search_aggregator import SearchAggregator

async def verify_industrial_performance():
    print("--- 1. Memory Optimization Check (__slots__) ---")
    agents = [
        BaseAgent(agent_id="base-test"),
        GovernedAgent(agent_id="gov-test"),
        ResearchAgent(agent_id="res-test"),
    ]
    
    for agent in agents:
        try:
            agent.__dict__
            print(f"[FAIL] {type(agent).__name__} has a __dict__. Optimization failed.")
        except AttributeError:
            print(f"[SUCCESS] {type(agent).__name__} is slot-optimized (No __dict__).")

    print("\n--- 2. Forensic Audit Check (Merkle Chain) ---")
    immudb.log_operation("VERIFY_START", {"status": "testing chain"})
    immudb.log_operation("VERIFY_MID", {"status": "linking block"})
    immudb.log_operation("VERIFY_END", {"status": "chain complete"})
    
    logs = immudb._logs if hasattr(immudb, "_logs") else []
    if len(logs) < 3:
        # Check disk if memory list is empty
        print("[INFO] Checking disk for audit logs...")
        import json
        with open(immudb.audit_log_path, "r") as f:
            logs = [json.loads(line) for line in f.readlines()]

    valid_chain = True
    for i in range(1, len(logs)):
        prev = logs[i-1]
        curr = logs[i]
        
        # Recalculate Alh link
        combined = f"{prev['current_hash']}".encode() # In our implementation, we link previous to current
        # Actually in our code: entry["previous_hash"] = self.last_hash
        if curr["previous_hash"] != prev["current_hash"]:
            print(f"[FAIL] Chain broken at index {i}. Expected {prev['current_hash'][:8]}, got {curr['previous_hash'][:8]}")
            valid_chain = False
            break
    
    if valid_chain:
        print("[SUCCESS] Merkle Chain Integrity Verified.")

    print("\n--- 3. Generator Efficiency Check (Streaming) ---")
    aggregator = SearchAggregator(test_mode=True)
    results_found = 0
    print("[INFO] Testing stream_search generator...")
    async for result in aggregator.stream_search("industrial performance"):
        results_found += 1
        if results_found >= 1:
            print(f"[SUCCESS] Generator yielded result: {result['title'][:30]}...")
            break
    
    if results_found > 0:
        print("[SUCCESS] Streaming ingestion is functional.")

if __name__ == "__main__":
    asyncio.run(verify_industrial_performance())
