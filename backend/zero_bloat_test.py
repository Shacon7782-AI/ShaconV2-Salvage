import time
import psutil
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.agents.researcher.scraper_tool import scrape_url

def benchmark_ingestion(url):
    print(f"Benchmarking Ingestion for: {url}")
    
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / 1024 / 1024
    
    start_time = time.time()
    result = scrape_url(url)
    end_time = time.time()
    
    end_mem = process.memory_info().rss / 1024 / 1024
    
    duration = end_time - start_time
    mem_delta = end_mem - start_mem
    
    if result:
        print(f"Title: {result['title']}")
        print(f"Content Length: {len(result['content'])} chars")
        print(f"Source: {result['source']}")
    
    print("-" * 30)
    print(f"Duration: {duration:.4f} seconds")
    print(f"Peak RAM Increase: {mem_delta:.2f} MB")
    print("-" * 30)
    
    return duration, mem_delta

if __name__ == "__main__":
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    benchmark_ingestion(test_url)
