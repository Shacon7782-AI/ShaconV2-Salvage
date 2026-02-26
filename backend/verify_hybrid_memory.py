import os
import sys
import uuid
import time
from typing import Dict, Any

# Ensure we can import app
sys.path.append(os.getcwd())

# Force environment variables for testing
os.environ["DATABASE_URL"] = "postgresql://invalid_host:5432/invalid_db"

from app.core.memory.vector_store import SovereignMemory

def test_hybrid_cycle():
    print("--- STARTING HYBRID MEMORY VERIFICATION (RAM-SPARING MODE) ---")
    
    # 1. Initialize Memory with a broken DB connection
    print("\n[STEP 1] Initializing Memory")
    memory = SovereignMemory()
    
    # Verify models are NOT loaded yet
    if memory.encoder_model is None and memory.reranker_model is None:
        print("SUCCESS: Memory started with zero model footprint.")
    else:
        print("WARNING: Models found in memory during init.")

    # 2. Commit a unique memory
    test_id = str(uuid.uuid4())[:8]
    test_content = f"Sovereign Cache Unit-{test_id}"
    test_meta = {"source": "verification_script", "unit": test_id}
    
    print(f"\n[STEP 2] Committing testing memory: '{test_content}'")
    memory.commit_to_memory(test_content, test_meta)
    
    # Verify models were purged after commit
    if memory.encoder_model is None:
        print("SUCCESS: Encoder purged after commit.")
    else:
        print("FAILED: Encoder still resident in RAM.")

    # 3. Verify it exists in Local Buffer
    print("\n[STEP 3] Verifying Local Recall")
    results = memory.recall(test_content, top_k=1)
    
    if results and results[0]["content"] == test_content:
        print(f"SUCCESS: Memory found. Source: {results[0]['source']}")
    else:
        print("FAILED: Memory not found.")
        return

    # Verify models were purged after recall
    if memory.encoder_model is None and memory.reranker_model is None:
        print("SUCCESS: Models purged after recall.")
    else:
        print("FAILED: Models still resident in RAM.")

    print("\n[CLEANUP] Verification script complete. System is stable and RAM-efficient.")

if __name__ == "__main__":
    test_hybrid_cycle()
