import sys
import json
from duckduckgo_search import DDGS

def search(query):
    results = []
    try:
        with DDGS() as ddgs:
            # Try different methods if one fails/returns empty, or just text
            ddg_gen = ddgs.text(query, max_results=5)
            if ddg_gen:
                for r in ddg_gen:
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body"),
                        "source": "duckduckgo"
                    })
    except Exception as e:
        # Print error to stderr so we don't break JSON on stdout
        print(f"Error: {e}", file=sys.stderr)
    
    print(json.dumps(results))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        search(query)
    else:
        print("[]")
