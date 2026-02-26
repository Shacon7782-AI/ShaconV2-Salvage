import asyncio
import os
import sys
import time

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.memory.prompt_compressor import compressor

async def verify_compression():
    print("=== LLMLingua-2 Compression Verification ===")
    
    # Simulate a long research context
    context = [
        "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals including humans. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.",
        "The various sub-fields of AI research are centered around particular goals and the use of particular tools. The traditional goals of AI research include reasoning, knowledge representation, planning, learning, natural language processing, perception, and the ability to move and manipulate objects.",
        "General intelligence (the ability to solve any problem) is among the field's long-term goals. To solve these problems, AI researchers have adapted and integrated a wide range of problem-solving techniques, including search and mathematical optimization, formal logic, artificial neural networks, and methods based on statistics, probability and economics.",
        "AI also draws upon computer science, psychology, linguistics, philosophy, and many other fields."
    ]
    
    query = "What are the traditional goals of AI research?"
    
    print(f"Original Context Length: {sum(len(c) for c in context)} chars")
    
    start_time = time.time()
    compressed = compressor.compress(
        context=context,
        instruction="Synthesize an answer for the query.",
        question=query,
        target_token=100 # Aggressive compression
    )
    duration = time.time() - start_time
    
    print("\n--- COMPRESSED PROMPT ---")
    print(compressed)
    print("-" * 30)
    print(f"Compressed Length: {len(compressed)} chars")
    print(f"Duration: {duration:.2f}s")
    
    # Check if key tokens are preserved
    keywords = ["reasoning", "knowledge representation", "planning", "learning", "natural language processing"]
    preserved = [k for k in keywords if k.lower() in compressed.lower()]
    
    print(f"\nKeywords Preserved: {len(preserved)}/{len(keywords)}")
    for k in preserved:
        print(f" - {k}")

    if len(preserved) >= 3:
        print("\nSUCCESS: Semantic integrity maintained under high compression.")
    else:
        print("\nWARNING: Some key information might have been lossed.")

if __name__ == "__main__":
    asyncio.run(verify_compression())
