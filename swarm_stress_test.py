
import asyncio
import os
import psutil
import time
from app.core.agents.base import BaseAgent
from app.core.immudb_sidecar import immudb
from app.core.agents.researcher.agent import ResearchAgent

async def run_swarm_stress_test(agent_count=50):
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)
    print(f"--- Swarm Mission Start: {agent_count} Agents ---")
    print(f"Initial Memory: {start_mem:.2f} MB")

    # 1. Spawn Swarm
    swarm = []
    for i in range(agent_count):
        # Use slots-optimized BaseAgent
        agent = BaseAgent(agent_id=f"drone-{i}")
        swarm.append(agent)
    
    mid_mem = process.memory_info().rss / (1024 * 1024)
    print(f"Swarm Spawned. Memory: {mid_mem:.2f} MB")
    print(f"Overhead per Agent: {(mid_mem - start_mem) / agent_count * 1024:.2f} KB")

    # 2. Forensic Load
    print("\n--- Generating Forensic Load ---")
    start_logs = 0
    if os.path.exists(immudb.audit_log_path):
        with open(immudb.audit_log_path, "r") as f:
            start_logs = len(f.readlines())

    for i in range(10):
        immudb.log_operation("SWARM_HEARTBEAT", {"swarm_size": len(swarm), "cycle": i})
    
    # 3. Verify Integrity
    if os.path.exists(immudb.audit_log_path):
        with open(immudb.audit_log_path, "r") as f:
            total_logs = len(f.readlines())
        
        is_consistent = immudb.consistency_proof(start_logs, total_logs - 1)
        print(f"Forensic Consistency: {'[SUCCESS]' if is_consistent else '[FAIL]'}")

    # 4. Cleanup
    swarm.clear()
    import gc
    gc.collect()
    end_mem = process.memory_info().rss / (1024 * 1024)
    print(f"Final Memory (Post-GC): {end_mem:.2f} MB")

if __name__ == "__main__":
    asyncio.run(run_swarm_stress_test(50))
