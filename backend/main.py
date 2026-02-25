from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

# App imports
from app.core.agents.orchestrator.agent import Orchestrator
from app.core.skills.base import SkillRegistry
from app.core.memory.vector_store import SovereignMemory

load_dotenv()

app = FastAPI(title="Shacon V2 API")

# Initialize core components
registry = SkillRegistry()
memory = SovereignMemory()
orchestrator = Orchestrator(registry=registry, sovereign_memory=memory, mock=True)

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
    return {"status": "Sovereign and Nominal"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
