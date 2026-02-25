from typing import List, Dict, Any, Optional
import json
import os
import asyncio
import re
from datetime import datetime
from app.core.telemetry import Blackboard
from app.core.llm_router import SwarmLLMRouter
from langchain_core.prompts import ChatPromptTemplate

class KnowledgeGraph:
    """
    A lightweight entity-relation mapping system for ShaconV2.
    Stores and retrieves structured context about the workspace.
    """
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            # Default to backend root regardless of CWD
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            storage_path = os.path.join(base_dir, "knowledge_graph.json")
            
        self.storage_path = storage_path
        self.entities = {} # entity_name -> metadata
        self.relations = [] # list of (entity_a, relation, entity_b)
        self.blackboard = Blackboard()
        self._load()

    async def update_from_blackboard(self):
        """
        Reads recent findings from the Blackboard and extracts structured knowledge.
        """
        findings = self.blackboard.get_recent_findings(limit=5)
        if not findings:
            return

        print(f"[KG] Syncing from {len(findings)} recent findings...")
        for finding in findings:
            content = finding.get("content", "")
            if not content:
                continue
            
            # Use LLM to extract entities and relations
            extracted = await self.extract_entities_from_text(content)
            print(f"[KG] Extracted {len(extracted.get('entities', []))} entities and {len(extracted.get('relations', []))} relations.")
            
            for entity in extracted.get("entities", []):
                print(f"[KG] Adding entity: {entity['name']}")
                self.add_entity(entity["name"], entity.get("properties", {}))
            
            for rel in extracted.get("relations", []):
                print(f"[KG] Adding relation: {rel['source']} {rel['relation']} {rel['target']}")
                self.add_relation(rel["source"], rel["relation"], rel["target"])

    async def extract_entities_from_text(self, text: str) -> Dict[str, Any]:
        """
        Uses a fast LLM pass to identify entities and relations.
        """
        # We use a structured LLM schema for extraction
        llm = SwarmLLMRouter.get_optimal_llm(structured_schema={
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "properties": {"type": "object"}
                        },
                        "required": ["name"]
                    }
                },
                "relations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "relation": {"type": "string"},
                            "target": {"type": "string"}
                        },
                        "required": ["source", "relation", "target"]
                    }
                }
            }
        })

        if not llm:
            return {"entities": [], "relations": []}

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract core Entities and their Relationships from the following finding. Return strictly a JSON object matching the requested schema."),
            ("human", "Finding Content: {text}")
        ])

        try:
            chain = prompt | llm
            # Using invoke instead of ainvoke as the router might return a non-async model interface depending on config
            # but ideally we want this to be async friendly.
            result = await chain.ainvoke({"text": text})
            return result
        except Exception as e:
            print(f"[KG] LLM Extraction failed: {e}. Falling back to Regex NLP.")
            return self._extract_via_regex(text)

    def _extract_via_regex(self, text: str) -> Dict[str, Any]:
        """
        Lightweight Regex-based entity extraction for when LLMs are unavailable.
        """
        entities = []
        relations = []
        
        # Simple entity matching: Look for capitalized words or phrases in quotes
        # e.g. "Neo-Tokyo", "Shacon", "St. Jude's"
        found_entities = re.findall(r'\"([^\"]+)\"|([A-Z][A-Za-z\-\']+(?: [A-Z][A-Za-z\-\']+)*)', text)
        for e in found_entities:
            name = e[0] or e[1]
            if name and name.lower() not in ["the", "a", "an", "is", "of", "and", "in", "to", "at"]:
                entities.append({"name": name, "properties": {"extracted_via": "regex"}})

        # Simple relation matching: Look for "source is/was/located in target"
        rel_matches = re.findall(r'([A-Z][a-z]+) (is|was|located in) ([A-Z][a-z]+)', text)
        for source, rel, target in rel_matches:
            relations.append({"source": source, "relation": rel, "target": target})

        return {"entities": entities, "relations": relations}

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
