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
        """
        timestamp = datetime.utcnow().isoformat()
        entry = {
            "timestamp": timestamp,
            "actor": actor,
            "operation": operation,
            "details": details,
            "previous_hash": self.last_hash
        }
        
        # Calculate current hash (Chain link)
        entry_str = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        entry["current_hash"] = current_hash
        
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            self.last_hash = current_hash
            print(f"[IMMUDB] Operation '{operation}' audited and locked. Hash: {current_hash[:8]}...")
        except Exception as e:
            print(f"[IMMUDB ERROR] Audit failure: {e}")

# Global Singleton
immudb = ImmudbSidecar()
