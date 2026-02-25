from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os

class Finding:
    def __init__(self, agent_id: str, content: str, related_mission_id: str = "general"):
        self.agent_id = agent_id
        self.content = content
        self.related_mission_id = related_mission_id
        self.timestamp = datetime.utcnow().isoformat()

class Blackboard:
    """
    A shared communication space for agents to post findings, insights, and telemetry.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Blackboard, cls).__new__(cls)
            cls._instance.findings = []
            cls._instance.insights = []
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            cls._instance.storage_path = os.path.join(base_dir, "memory_blackboard.json")
        return cls._instance

    def post_finding(self, agent_id: str, content: str, related_mission_id: str = "general"):
        """Post a raw discovery or data point."""
        finding = {
            "agent_id": agent_id,
            "content": content,
            "related_mission_id": related_mission_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "finding"
        }
        self.findings.append(finding)
        print(f"[BLACKBOARD] Finding posted by {agent_id}: {content[:100]}...")
        self._persist()

    def post_insight(self, agent_id: str, summary: str):
        """Post a high-level semantic insight (used by Scout/Researcher)."""
        insight = {
            "agent_id": agent_id,
            "content": summary,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "insight"
        }
        self.insights.append(insight)
        print(f"[BLACKBOARD] Insight posted by {agent_id}: {summary[:100]}...")
        self._persist()

    def get_recent_findings(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.findings[-limit:]

    def get_recent_insights(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.insights[-limit:]

    def _persist(self):
        """Save blackboard state to disk for cross-process observation (optional but helpful)."""
        try:
            data = {
                "findings": self.findings[-100:], # Cap for now
                "insights": self.insights[-50:]
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[BLACKBOARD] Persistence failed: {e}")
