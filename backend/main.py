from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

# App imports
from app.core.agents.orchestrator.agent import Orchestrator
from app.core.skills.base import SkillRegistry
from app.core.skills.precision.deep_research import DeepResearchSkill
from app.core.memory.vector_store import SovereignMemory
from app.core.agents.scout.agent import ScoutAgent

from contextlib import asynccontextmanager
from app.core.memory.dropzone_watcher import start_watcher

# Global reference to keep watcher alive
dropzone_observer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dropzone_observer
    dropzone_dir = os.path.join(os.path.dirname(__file__), "data_dropzone")
    print(f"[BOOT] Initializing Sovereign Dropzone Watcher at {dropzone_dir}")
    dropzone_observer = start_watcher(dropzone_dir)
    yield
    print("[SHUTDOWN] Stopping Sovereign Dropzone Watcher")
    if dropzone_observer:
        dropzone_observer.stop()
        dropzone_observer.join()

app = FastAPI(title="Shacon V2 API", lifespan=lifespan)

# Initialize core components
registry = SkillRegistry()
registry.register(DeepResearchSkill())
memory = SovereignMemory()
orchestrator = Orchestrator(registry=registry, sovereign_memory=memory, mock=True)
scout = ScoutAgent(mock=True)

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Step 1: Orchestrator reasons about the intent
        step = await orchestrator.reason(request.message, request.history)
        
        # In a real loop, we would execute steps until COMPLETE.
        # For the Phase 3.1 wiring check, we execute the first step.
        result = await orchestrator.execute_step(step)
        
        return {
            "thinking": step.thinking,
            "action": step.action,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health():
    return scout.analyze_environment()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
