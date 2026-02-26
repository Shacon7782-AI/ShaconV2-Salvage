import chromadb
try:
    client = chromadb.PersistentClient(path="./test_chroma")
    print("ChromaDB Initialized Successfully")
except Exception as e:
    print(f"ChromaDB Initialization Failed: {e}")
    import traceback
    traceback.print_exc()
