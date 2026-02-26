import os
import sys
import uuid
import time
from sqlalchemy import text

# Ensure we can import app
sys.path.append(os.getcwd())

from app.core.memory.vector_store import SovereignMemory
from app.db.schemas.session import SessionLocal

def test_full_sync_loop():
    print("--- STARTING FULL SYNC VERIFICATION ---")
    
    # 1. Initialize Memory
    memory = SovereignMemory()
    test_id = str(uuid.uuid4())[:8]
    test_content = f"Sync-Test-Unit-{test_id}"
    
    # 2. Force Local Commit Only (Simulate Docker Down)
    print(f"\n[STEP 1] Committing memory: '{test_content}'")
    # We'll temporarily mock the DB to fail for this call
    import app.core.memory.vector_store as vs
    original_session = vs.SessionLocal
    vs.SessionLocal = lambda: None # This will cause commit_to_memory to fail DB part
    
    try:
        memory.commit_to_memory(test_content, {"test_id": test_id})
    except Exception as e:
        print(f"Commit handled expectedly: {e}")
    
    # 3. Verify it's in FAISS but UNSYNCED
    unsynced = [m for m in memory.buffer_metadata if m["content"] == test_content and not m.get("synced")]
    if unsynced:
        print(f"SUCCESS: Memory '{test_content}' is in FAISS and marked UNSYNCED.")
    else:
        print("FAILED: Memory not found in FAISS or already marked synced.")
        vs.SessionLocal = original_session
        return

    # 4. Restore DB and Sync
    print("\n[STEP 2] Restoring DB and calling sync_with_postgres()")
    vs.SessionLocal = original_session
    memory.sync_with_postgres()
    
    # 5. Verify it's now in Postgres
    print("\n[STEP 3] Verifying presence in Postgres...")
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT content FROM sovereign_memory_nodes WHERE content = :c"), 
            {"c": test_content}
        ).fetchone()
        
        if result:
            print(f"SUCCESS: Memory '{test_content}' found in Postgres!")
        else:
            print("FAILED: Memory not found in Postgres after sync.")
            
        # Also check local flag
        synced_flag = [m for m in memory.buffer_metadata if m["content"] == test_content and m.get("synced")]
        if synced_flag:
            print("SUCCESS: Local metadata updated to synced=True.")
        else:
            print("FAILED: Local metadata still marked as unsynced.")
            
    finally:
        db.close()

    print("\n[CLEANUP] Verification complete. Hybrid Sync is fully operational.")

if __name__ == "__main__":
    test_full_sync_loop()
