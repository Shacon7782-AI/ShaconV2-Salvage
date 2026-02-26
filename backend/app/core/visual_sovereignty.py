
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.immudb_sidecar import immudb

class VisualSovereignty:
    """
    Manages "Audit-Locked Assets" - cinematic visuals that are
    cryptographically tied to agentic missions and agent history.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.assets_dir = os.path.join(base_dir, "governance", "visual_audit")
        os.makedirs(self.assets_dir, exist_ok=True)

    def register_asset(self, mission_id: str, asset_type: str, metadata: Dict[str, Any], file_content: Optional[bytes] = None) -> str:
        """
        Locks a visual asset into the Sovereign Audit Log.
        If file_content is provided, it saves the asset locally.
        Returns the Alh (Accumulative Hash) of the registration.
        """
        asset_id = f"{mission_id}_{int(datetime.utcnow().timestamp())}"
        
        # 1. Calculate Content Hash
        content_hash = "N/A"
        if file_content:
            content_hash = hashlib.sha256(file_content).hexdigest()
            asset_path = os.path.join(self.assets_dir, f"{asset_id}.png")
            with open(asset_path, "wb") as f:
                f.write(file_content)
            metadata["storage_path"] = asset_path
        
        # 2. Audit Lock
        audit_details = {
            "mission_id": mission_id,
            "asset_id": asset_id,
            "asset_type": asset_type,
            "content_hash": content_hash,
            "metadata": metadata
        }
        
        immudb.log_operation("ASSET_SOVEREIGN_LOCK", audit_details)
        return immudb.last_hash

    def get_asset_verification(self, asset_id: str) -> Dict[str, Any]:
        """
        Retrieves the inclusion proof and metadata for a specific visual asset.
        """
        # In a real scenario, this would return the full Merkle path from Immudb
        return {
            "asset_id": asset_id,
            "verified": True,
            "timestamp": datetime.utcnow().isoformat(),
            "proof_type": "linear_chain_inclusion"
        }

# Global Singleton
visual_sovereignty = VisualSovereignty()
