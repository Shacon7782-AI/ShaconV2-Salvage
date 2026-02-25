
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Sanity check passed"}

@app.get("/api/dashboard/graph")
def graph():
    return {"entities": [], "relations": []}

@app.get("/api/dashboard/telemetry")
def telemetry():
    return {"findings": [], "insights": []}

if __name__ == "__main__":
    print("[SANITY] Starting on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
