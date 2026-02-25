from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime

class KnowledgeGraph:
    """
    A lightweight entity-relation mapping system for ShaconV2.
    Stores and retrieves structured context about the workspace.
    """
    def __init__(self, storage_path: str = "backend/knowledge_graph.json"):
        self.storage_path = storage_path
        self.entities = {} # entity_name -> metadata
        self.relations = [] # list of (entity_a, relation, entity_b)
        self._load()

    def add_entity(self, name: str, properties: Dict[str, Any]):
        self.entities[name] = {
            **properties,
            "updated_at": datetime.utcnow().isoformat()
        }
        self._save()

    def add_relation(self, source: str, relation: str, target: str):
        self.relations.append({
            "source": source,
            "relation": relation,
            "target": target,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._save()

    def query(self, entity_name: str) -> Dict[str, Any]:
        """Retrieve an entity and its connections."""
        data = self.entities.get(entity_name, {})
        connections = [r for r in self.relations if r["source"] == entity_name or r["target"] == entity_name]
        return {
            "entity": data,
            "connections": connections
        }

    def _save(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump({"entities": self.entities, "relations": self.relations}, f, indent=2)
        except Exception as e:
            print(f"[KG] Save failed: {e}")

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.entities = data.get("entities", {})
                    self.relations = data.get("relations", [])
            except Exception as e:
                print(f"[KG] Load failed: {e}")
