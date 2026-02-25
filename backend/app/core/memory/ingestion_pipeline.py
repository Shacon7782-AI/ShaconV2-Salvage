import os
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_community.document_loaders import PyPDFLoader
from app.core.memory.vector_store import SovereignMemory
from app.core.telemetry import Blackboard
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# We use the system's SovereignMemory for unified embedding and schema
memory = SovereignMemory()
blackboard = Blackboard()

def process_file(filepath: str):
    """
    Ingests a single file into the local PostgreSQL Vector database.
    """
    print(f"\n[INGESTION] Starting file processing: {filepath}")
    
    # 1. Load the document based on extension
    if filepath.endswith('.md'):
        loader = UnstructuredMarkdownLoader(filepath)
    elif filepath.endswith('.txt'):
        loader = TextLoader(filepath)
    elif filepath.endswith('.pdf'):
        loader = PyPDFLoader(filepath)
    else:
        print(f"[INGESTION ERROR] Unsupported file format: {filepath}")
        return
        
    try:
        documents = loader.load()
        print(f"[INGESTION] Loaded {len(documents)} pages/sections from {os.path.basename(filepath)}")
    except Exception as e:
        print(f"[INGESTION ERROR] Failed to load {filepath}: {e}")
        return

    # 2. Extract text and embed using SovereignMemory
    print(f"[INGESTION] Generating embeddings and saving to local database...")
    try:
        total_chunks = 0
        for doc in documents:
            content = doc.page_content
            metadata = {
                "source_file": os.path.basename(filepath),
                "type": "dropzone_ingestion"
            }
            # SovereignMemory handles chunking automatically
            memory.commit_to_memory(content, metadata)
            
            # Post discovery to Blackboard for Knowledge Graph extraction
            blackboard.post_finding("IngestionPipeline", f"Processed data from {os.path.basename(filepath)}")
            
            total_chunks += 1
            
        print(f"[INGESTION SUCCESS] Successfully ingested {os.path.basename(filepath)} into Sovereign Memory.")
        
    except Exception as e:
        print(f"[INGESTION ERROR] Failed to save to database: {e}")

if __name__ == "__main__":
    # Test script 
    print("Testing Ingestion Pipeline Initialization")
