from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os
import subprocess
import asyncio
from dotenv import load_dotenv

# Load environment variables FIRST before any local imports
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# App imports
from app.core.agents.orchestrator.agent import Orchestrator
from app.core.skills.base import SkillRegistry
from app.core.skills.precision.deep_research import DeepResearchSkill
from app.core.skills.precision.cloud_researcher import CloudResearcherSkill
from app.core.memory.vector_store import SovereignMemory
from app.core.agents.scout.agent import ScoutAgent
from app.core.knowledge_graph import KnowledgeGraph
from app.core.telemetry import Blackboard
from app.core.agents.researcher.mission_control import MissionControl
from app.db.schemas.session import SessionLocal
from app.db.schemas.models import SovereignMemoryNode
from app.core.memory.dropzone_watcher import start_watcher

# Initialize core components
registry = SkillRegistry()
registry.register(DeepResearchSkill())
registry.register(CloudResearcherSkill())
memory = SovereignMemory()
orchestrator = Orchestrator(registry=registry, sovereign_memory=memory, mock=False)
scout = ScoutAgent(mock=False)
kg = KnowledgeGraph()
blackboard = Blackboard()

# Global reference to keep watcher alive
dropzone_observer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global dropzone_observer
    
    # 1. Start Dropzone Watcher
    dropzone_dir = os.path.join(os.path.dirname(__file__), "data_dropzone")
    print(f"[BOOT] Initializing Sovereign Dropzone Watcher at {dropzone_dir}")
    dropzone_observer = start_watcher(dropzone_dir)

    # 2. Sovereign LLM Check (Skipped in Phase 8 for memory safety)
    print(f"[BOOT] Cloud-Delegated Mode: Skipping heavy local LLM checks to preserve RAM.")

    # 3. Start 24/7 Perpetual Ingestion Loop (KG Sync)
    async def perpetual_sync():
        print("[SENTINEL] Activating 24/7 Perpetual Ingestion Loop...")
        while True:
            try:
                await kg.update_from_blackboard()
                await asyncio.sleep(60) # Sync every minute
            except Exception as e:
                print(f"[SENTINEL ERROR] Perpetual sync failed: {e}")
                await asyncio.sleep(10)

    sync_task = asyncio.create_task(perpetual_sync())

    # 4. Start 24/7 Mission-Driven Perpetual Researcher
    async def perpetual_researcher():
        print("[SENTINEL] Activating 24/7 Perpetual Researcher Loop...")
        mission_control = MissionControl()
        cloud_researcher = registry.get_skill("cloud_research")
        
        while True:
            try:
                mission = mission_control.get_active_mission()
                if mission and mission.get("status") == "pending":
                    print(f"[RESEARCHER] Starting Mission: {mission['name']}")
                    
                    # Execute queries in the mission
                    for query in mission.get("queries", []):
                        print(f"[RESEARCHER] Sub-task: {query}")
                        await cloud_researcher.execute({"query": query, "mission_id": mission["id"]})
                        # Breath between queries to avoid rate limits and memory spikes
                        await asyncio.sleep(30) 
                    
                    mission_control.advance_mission()
                    print(f"[RESEARCHER] Mission {mission['id']} completed.")
                
                # Check for new missions every 10 minutes if queue is empty or active is done
                await asyncio.sleep(600)
            except Exception as e:
                print(f"[RESEARCHER ERROR] Perpetual research failed: {e}")
                await asyncio.sleep(60)

    research_task = asyncio.create_task(perpetual_researcher())

    yield
    print("[SHUTDOWN] Stopping Sentinel Systems")
    sync_task.cancel()
    research_task.cancel()
    if dropzone_observer:
        dropzone_observer.stop()
        dropzone_observer.join()

app = FastAPI(title="Shacon V2 API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
registry = SkillRegistry()
registry.register(DeepResearchSkill())
registry.register(CloudResearcherSkill())
memory = SovereignMemory()
orchestrator = Orchestrator(registry=registry, sovereign_memory=memory, mock=False)
scout = ScoutAgent(mock=False)
kg = KnowledgeGraph()
blackboard = Blackboard()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        print(f"[CHAT] Received message: {request.message}")
        orchestrator.reset_memory()
        history = request.history
        
        # Loop over orchestration steps until a blocking action (DISCUSS/COMPLETE)
        max_internal_steps = 5
        last_step = None
        last_result = None
        
        for i in range(max_internal_steps):
            print(f"[CHAT] Step {i+1} reasoning...")
            step = await orchestrator.reason(request.message, history)
            last_step = step
            print(f"[CHAT] Action: {step.action} | Thinking: {step.thinking[:100]}...")
            
            if step.action == "DISCUSS" or step.action == "COMPLETE":
                # Final response to user
                res = await orchestrator.execute_step(step)
                return {
                    "thinking": step.thinking,
                    "action": step.action,
                    "result": res.get("prompt") if step.action == "DISCUSS" else res.get("status")
                }
            
            # Execute skill and continue loop
            print(f"[CHAT] Executing Skill: {step.skill_name}")
            last_result = await orchestrator.execute_step(step)
            # Result is added to orchestrator.memory for the next reasoning cycle
            
        return {
            "thinking": last_step.thinking if last_step else "Iteration limit reached.",
            "action": last_step.action if last_step else "HALT",
            "result": last_result or "Process incomplete."
        }
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health():
    return scout.analyze_environment()

@app.get("/api/dashboard/graph")
def get_graph():
    return {
        "entities": list(kg.entities.keys()),
        "relations": kg.relations
    }

@app.get("/api/dashboard/telemetry")
def get_telemetry():
    return {
        "findings": blackboard.get_recent_findings(limit=20),
        "insights": blackboard.get_recent_insights(limit=10)
    }

@app.get("/api/dashboard/memory")
def get_memory():
    db = SessionLocal()
    try:
        nodes = db.query(SovereignMemoryNode).order_by(SovereignMemoryNode.created_at.desc()).limit(10).all()
        return [
            {
                "content": n.content,
                "metadata": n.metadata_json,
                "created_at": n.created_at.isoformat()
            } for n in nodes
        ]
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
