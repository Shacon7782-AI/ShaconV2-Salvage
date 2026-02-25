import json
import os
from typing import List, Dict, Any, Optional

class MissionControl:
    """
    Manages the 24/7 Research Mission Queue.
    Handles persistence and mission state transitions.
    """
    def __init__(self, missions_file: str = "missions.json"):
        self.missions_file = missions_file
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.missions_file):
            try:
                with open(self.missions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MISSION CONTROL] Error loading missions: {e}")
        
        return {"active_mission_index": 0, "missions": []}

    def _save(self):
        try:
            with open(self.missions_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[MISSION CONTROL] Error saving missions: {e}")

    def get_active_mission(self) -> Optional[Dict[str, Any]]:
        idx = self.data.get("active_mission_index", 0)
        missions = self.data.get("missions", [])
        if 0 <= idx < len(missions):
            return missions[idx]
        return None

    def advance_mission(self):
        """Moves to the next mission and saves state."""
        idx = self.data.get("active_mission_index", 0)
        missions = self.data.get("missions", [])
        
        # Mark current as completed if it exists
        if 0 <= idx < len(missions):
            missions[idx]["status"] = "completed"
            
        self.data["active_mission_index"] = idx + 1
        self._save()

    def add_mission(self, name: str, objective: str, queries: List[str], priority: str = "Medium"):
        new_mission = {
            "id": f"MISSION_{len(self.data['missions']) + 1:02d}",
            "name": name,
            "objective": objective,
            "queries": queries,
            "priority": priority,
            "status": "pending"
        }
        self.data["missions"].append(new_mission)
        self._save()
