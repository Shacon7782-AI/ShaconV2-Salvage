import asyncio
import time
import random
import sys
import os
from typing import List, Dict, Any

# Ensure we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.core.triage import SovereignTriage
from app.core.immudb_sidecar import immudb

# Define a set of 20 randomized enterprise/technical intents
INTENTS = [
    "Analyze the risk profile of our quarterly revenue projections.",
    "Debug the race condition in the asynchronous log aggregator.",
    "Optimize the memory reclamation strategy for WSL2 in ShaconV2.",
    "Draft a legal disclaimer for autonomous agent deployment.",
    "Synthesize the BGE vs Jina reranker benchmarks for a real-time system.",
    "Evaluate the F1 score of Llama 3.1 405B on classification tasks.",
    "Map the dependency graph of the frontend visualization skill.",
    "Audit the immudb consistency proofs for the last 100 operations.",
    "Execute a deep research mission on LPU cost reduction strategies.",
    "Configure a high-concurrency stress test for the triage engine.",
    "Detect anomalies in the hardware offloading telemetry.",
    "Generate a summary of the Enterprise Benchmarking Report.",
    "Propose a self-healing protocol for broken agentic imports.",
    "Validate the 16-phase sovereign triage mapping accuracy.",
    "Research the performance delta between Groq and Cloud GPUs.",
    "Lock the core skill registry and verify boot sequence.",
    "Analyze the impact of quantization on FAISS k-NN lookups.",
    "Predict the failure points of a hybrid GPU/XPU architecture.",
    "Reconstitute an agent's state from the durable recovery log.",
    "Scale the sovereign memory nodes to support 1M entities."
]

async def concurrent_triage(intents: List[str]):
    triage = SovereignTriage()
    tasks = []
    
    print(f"\n--- [STRESS TEST: STARTING 50 CONCURRENT TRIAGE REQUESTS] ---")
    start_time = time.perf_counter()
    
    # We will pick 50 intents (some duplicates) to hammer the system
    test_batch = [random.choice(intents) for _ in range(50)]
    
    for i, intent in enumerate(test_batch):
        # We don't use real LLM networking here if we want pure logic stress, 
        # but SovereignTriage.execute_triage() calls the LLM router.
        # We'll see how it handles the throughput.
        tasks.append(triage.execute_triage(f"TEST_{i}: {intent}"))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print(f"--- [STRESS TEST: COMPLETED] ---")
    print(f"Total Intents: {len(test_batch)}")
    print(f"Total Time: {duration:.2f}s")
    print(f"Avg Latency: {(duration/len(test_batch))*1000:.2f}ms per request")
    
    success_count = 0
    error_count = 0
    for res in results:
        if isinstance(res, Exception):
            error_count += 1
        else:
            success_count += 1
            
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    
    # Verify immudb growth
    history = immudb.get_logs(limit=60)
    print(f"Audit Trail Entries (last 60): {len(history)}")
    
    if error_count == 0 and success_count == len(test_batch):
        print("\n[VERDICT] STRESS TEST PASSED: Sovereign Triage is concurrent-stable.")
    else:
        print("\n[VERDICT] STRESS TEST FAILED: Concurrency issues detected.")

if __name__ == "__main__":
    asyncio.run(concurrent_triage(INTENTS))
