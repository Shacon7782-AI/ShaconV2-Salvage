
import os
from dotenv import load_dotenv
load_dotenv()

keys = ["GOOGLE_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY", "SERPER_API_KEY"]
print("--- ENVIRONMENT AUDIT ---")
for k in keys:
    val = os.getenv(k)
    print(f"{k}: {'PRESENT' if val else 'MISSING'}")

# Check local LLM
import requests
print("\n--- OLLAMA CHECK ---")
try:
    res = requests.get("http://localhost:11434/api/tags", timeout=2)
    print(f"Ollama Status: {res.status_code}")
    print(f"Ollama Models: {res.json()}")
except Exception as e:
    print(f"Ollama Connection Failed: {e}")
