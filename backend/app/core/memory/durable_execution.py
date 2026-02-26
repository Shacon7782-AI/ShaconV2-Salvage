import json
from typing import Dict, Any, Optional
from app.core.immudb_sidecar import immudb

class DurableContext:
    """
    Enables durable execution by persisting task state to high-integrity storage.
    If an agent crashes mid-task, it can recover from the last signed step.
    """
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.state: Dict[str, Any] = {"step": 0, "context": {}}

    def checkpoint(self, step_name: str, data: Any):
        """Creates a signed checkpoint of the current execution state."""
        self.state["step"] += 1
        self.state["context"][step_name] = data
        
        # Log to immutable audit log for durability
        entry = {
            "task_id": self.task_id,
            "step": self.state["step"],
            "name": step_name,
            "data": data
        }
        immudb.log_operation("DURABLE_CHECKPOINT", entry)
        print(f"[DURABLE] Checkpoint '{step_name}' secured for Task {self.task_id}.")

    @classmethod
    def recover(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Recovers the last known state for a specific task via immudb audit logs."""
        print(f"[DURABLE] Searching for recovery state for Task {task_id}...")
        
        # Query the immudb audit log for latest step
        logs = immudb.get_logs(limit=100) # Simple scan reverse chronological
        latest_step = -1
        last_state = None
        
        # Filter for this task and find the highest step number
        for entry in reversed(logs):
            details = entry.get("details", {})
            if details.get("task_id") == task_id:
                step = details.get("step", 0)
                if step > latest_step:
                    latest_step = step
                    last_state = details
                    
        if last_state:
            print(f"[DURABLE] SUCCESS: Found state at Step {latest_step}. Reconstituting...")
            return last_state
            
        print(f"[DURABLE] No recovery state found for Task {task_id}.")
        return None
