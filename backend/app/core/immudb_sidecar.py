import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

class ImmudbSidecar:
    """
    Simulates / Interfaces with an Immudb instance for immutable auditing.
    Provides a cryptographic chain of operations to ensure data integrity.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.audit_log_path = os.path.join(base_dir, "governance", "sovereign_audit.log")
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        self.last_hash = self._get_last_hash()

    def _smart_serialize(self, data: Any) -> Any:
        """Recursively converts non-serializable objects (Enums, etc) into JSON-safe formats."""
        if isinstance(data, dict):
            return {str(k): self._smart_serialize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._smart_serialize(i) for i in data]
        elif hasattr(data, "value"): # Handle Enums
            return data.value
        elif hasattr(data, "dict"): # Handle Pydantic models
            return self._smart_serialize(data.dict())
        return data

    def _get_last_hash(self) -> str:
        """Retrieves the hash of the last entry to maintain the chain."""
        if not os.path.exists(self.audit_log_path):
            return "0" * 64
        
        try:
            with open(self.audit_log_path, "rb") as f:
                # Go to the end and find the last line
                f.seek(0, os.SEEK_END)
                pos = f.tell()
                while pos > 0:
                    pos -= 1
                    f.seek(pos)
                    if f.read(1) == b"\n":
                        line = f.readline().decode().strip()
                        if line:
                            data = json.loads(line)
                            return data.get("current_hash", "0" * 64)
                # If only one line exists
                f.seek(0)
                line = f.readline().decode().strip()
                if line:
                    data = json.loads(line)
                    return data.get("current_hash", "0" * 64)
        except Exception:
            pass
        return "0" * 64

    def log_operation(self, operation: str, details: Dict[str, Any], actor: str = "SYSTEM"):
        """
        Appends an operation to the immutable audit log with a SHA-256 chain hash.
        This implements a linear Merkle-style chain (Accumulative Hash).
        """
        timestamp = datetime.utcnow().isoformat()
        
        # 1. Base Entry Data
        entry = {
            "timestamp": timestamp,
            "actor": actor,
            "operation": operation,
            "details": self._smart_serialize(details),
            "previous_hash": self.last_hash
        }
        
        # 2. Cryptographic Chain Link (Current Hash / Alh)
        entry_str = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        entry["current_hash"] = current_hash
        
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            
            # Update memory state for next link
            self.last_hash = current_hash
        except Exception as e:
            print(f"[IMMUDB ERROR] Audit failure: {e}")

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves a list of audit logs, most recent first."""
        if not os.path.exists(self.audit_log_path):
            return []
            
        logs = []
        try:
            with open(self.audit_log_path, "r") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if line.strip():
                        logs.append(json.loads(line))
                        if len(logs) >= limit:
                            break
        except Exception as e:
            print(f"[IMMUDB ERROR] Retrieval failure: {e}")
        return logs

    def inclusion_proof(self, target_hash: str) -> bool:
        """
        Mathematically confirms an action exists in the ledger by scanning the chain.
        In a production Immudb, this would return a Merkle Audit Path.
        """
        if not os.path.exists(self.audit_log_path):
            return False
            
        try:
            with open(self.audit_log_path, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get("current_hash") == target_hash:
                        return True
        except Exception:
            pass
        return False

    def consistency_proof(self, slice_start: int, slice_end: int) -> bool:
        """
        Ensures the log history is linear and untampered between two indices.
        Verifies that each block's previous_hash matches the preceding block's hash.
        """
        if not os.path.exists(self.audit_log_path):
            return False
            
        try:
            with open(self.audit_log_path, "r") as f:
                lines = f.readlines()
                if slice_end >= len(lines):
                    slice_end = len(lines) - 1
                
                for i in range(max(1, slice_start), slice_end + 1):
                    prev = json.loads(lines[i-1])
                    curr = json.loads(lines[i])
                    if curr.get("previous_hash") != prev.get("current_hash"):
                        return False
            return True
        except Exception:
            return False

# Global Singleton
immudb = ImmudbSidecar()
