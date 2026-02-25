import requests
import json

response = requests.get("https://openrouter.ai/api/v1/models")
models = response.json().get("data", [])
free_models = [m["id"] for m in models if "free" in m["id"].lower() and "llama" in m["id"].lower()]
print("\n".join(free_models))
