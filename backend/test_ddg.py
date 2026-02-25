from duckduckgo_search import DDGS
import json

try:
    with DDGS() as ddgs:
        results = list(ddgs.text("agent swarms", max_results=3))
        print(json.dumps(results, indent=2))
except Exception as e:
    print(f"FAILED: {e}")
