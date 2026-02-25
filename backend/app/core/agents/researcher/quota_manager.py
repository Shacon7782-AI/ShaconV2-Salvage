import json
import os
from datetime import datetime
from typing import Dict, Any

USAGE_FILE = "search_usage.json"

class QuotaManager:
    """
    Manages search API text quotas to prioritize free tiers.
    Usage is persisted to 'search_usage.json'.
    
    Limits:
    - Google: 100/day
    - Serper: 2500/month
    - Tavily: 1000/month
    - Exa: 1000/month
    - SearchApi: 100/month (If added)
    - DuckDuckGo: Unlimited
    """
    
    LIMITS = {
        "google": {"limit": 100, "period": "day"},
        "serper": {"limit": 2500, "period": "month"},
        "tavily": {"limit": 1000, "period": "month"},
        "exa": {"limit": 1000, "period": "month"},
        "searchapi": {"limit": 100, "period": "month"},
        "duckduckgo": {"limit": float('inf'), "period": "none"}
    }

    def __init__(self):
        self.usage_file = USAGE_FILE
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._init_data()

    def _init_data(self) -> Dict[str, Any]:
        return {
            "google": {"count": 0, "last_reset": datetime.now().isoformat()},
            "serper": {"count": 0, "last_reset": datetime.now().isoformat()},
            "tavily": {"count": 0, "last_reset": datetime.now().isoformat()},
            "exa": {"count": 0, "last_reset": datetime.now().isoformat()},
            "duckduckgo": {"count": 0, "last_reset": datetime.now().isoformat()}
        }

    def _save_data(self):
        with open(self.usage_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def _check_reset(self, provider: str):
        if provider not in self.LIMITS or self.LIMITS[provider]["period"] == "none":
            return

        last_reset = datetime.fromisoformat(self.data[provider]["last_reset"])
        now = datetime.now()
        period = self.LIMITS[provider]["period"]

        should_reset = False
        if period == "day":
            if now.date() > last_reset.date():
                should_reset = True
        elif period == "month":
            if now.month != last_reset.month or now.year != last_reset.year:
                should_reset = True

        if should_reset:
            self.data[provider]["count"] = 0
            self.data[provider]["last_reset"] = now.isoformat()
            self._save_data()

    def can_use(self, provider: str) -> bool:
        """Returns True if the provider has remaining quota."""
        if provider not in self.data:
            self.data[provider] = {"count": 0, "last_reset": datetime.now().isoformat()}
        
        self._check_reset(provider)
        
        limit = self.LIMITS.get(provider, {}).get("limit", 0)
        current = self.data[provider]["count"]
        
        return current < limit

    def increment(self, provider: str):
        """Increments usage count for a provider."""
        if provider in self.data:
            self.data[provider]["count"] += 1
            self._save_data()

    def get_status(self) -> str:
        """Returns a formatted status string of current usage."""
        status = []
        for p, info in self.data.items():
            limit = self.LIMITS.get(p, {}).get("limit", "N/A")
            status.append(f"{p.title()}: {info['count']}/{limit}")
        return " | ".join(status)
