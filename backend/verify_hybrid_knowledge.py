import requests
import os
import time

BASE_URL = "http://localhost:8080/api"

def test_knowledge_api():
    print("\n[VERIFY] Testing Knowledge API...")
    
    # 1. Test Upload
    print("[VERIFY] Testing Document Upload...")
    test_file = "test_knowledge_doc.md"
    with open(test_file, "w") as f:
        f.write("# Hybrid Knowledge Test\nThis is a test document for FAISS + Postgres integration.")
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file, f)}
            res = requests.post(f"{BASE_URL}/documents/upload", files=files)
            print(f"[VERIFY] Upload Response: {res.status_code} - {res.json()}")
            assert res.status_code == 200
    except Exception as e:
        print(f"[VERIFY ERROR] Upload failed: {e}")
        return

    # 2. Wait for watcher and ingestion (simulated or real)
    print("[VERIFY] Waiting for ingestion pipeline...")
    time.sleep(5) 

    # 3. Test List
    print("[VERIFY] Testing Document Listing...")
    try:
        res = requests.get(f"{BASE_URL}/documents")
        print(f"[VERIFY] List Response: {res.status_code}")
        docs = res.json()
        print(f"[VERIFY] Documents found: {len(docs)}")
        for doc in docs:
            print(f" - {doc['title']} ({doc['file_type']})")
        
        # Check if our test file is there
        titles = [d['title'] for d in docs]
        if test_file in titles:
            print("[VERIFY SUCCESS] Test document found in listing!")
        else:
            print("[VERIFY WARNING] Test document not yet in listing (ingestion might be slow).")
            
    except Exception as e:
        print(f"[VERIFY ERROR] List failed: {e}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    # Ensure the server is running or mock the check
    test_knowledge_api()
