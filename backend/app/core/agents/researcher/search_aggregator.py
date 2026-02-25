import os
import json
import requests
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
from tavily import TavilyClient
from exa_py import Exa
from sqlalchemy.orm import Session
from .quota_manager import QuotaManager
from .provider_router import ProviderRouter

class SearchAggregator:
    """
    Implements Intelligent Query Routing with Quota Tracking and Persistence.
    
    Routes queries to optimal providers based on query type:
    - code: Serper → Exa → SearchApi → Tavily
    - news: Serper → SearchApi → Tavily → Google
    - research: Tavily → Exa → Serper → SearchApi
    - technical: Exa → Tavily → Serper → SearchApi
    - general: Serper → Tavily → Exa → SearchApi
    
    DuckDuckGo serves as unlimited fallback for all types.
    
    When db session is provided:
    - Checks cache before making API calls (saves tokens)
    - Stores results after successful searches (builds knowledge)
    """

    def __init__(self, db: Optional[Session] = None, test_mode: bool = False):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.exa_api_key = os.getenv("EXA_API_KEY")
        self.searchapi_api_key = os.getenv("SEARCHAPI_API_KEY")
        self.quota = QuotaManager()
        self.router = ProviderRouter()
        self.db = db
        self.test_mode = test_mode  # Use DDG first for testing (saves API tokens)
        self._repository = None
        
        # Initialize repository if db provided
        if db:
            from .research_repository import ResearchRepository
            self._repository = ResearchRepository(db)
        
        # Map provider names to their search methods and key requirements
        self._providers = {
            "google": (self._search_google, lambda: self.google_api_key and self.google_cse_id),
            "serper": (self._search_serper, lambda: self.serper_api_key),
            "tavily": (self._search_tavily, lambda: self.tavily_api_key),
            "exa": (self._search_exa, lambda: self.exa_api_key),
            "searchapi": (self._search_searchapi, lambda: self.searchapi_api_key),
            "duckduckgo": (self._search_duckduckgo, lambda: True),  # Always available
        }

    async def search(self, query: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Search using intelligent routing based on query type.
        Falls back through providers until one succeeds.
        
        Args:
            query: Search query
            use_cache: If True and db is available, check cache first
            
        Returns:
            List of result dicts
        """
        print(f"[SearchAggregator] Status: {self.quota.get_status()}")
        
        # Get query classification
        query_type, confidence = self.router.classifier.classify(query)
        
        # Check cache if available
        if use_cache and self._repository:
            cached = self._repository.find_cached_results(query)
            if cached:
                print(f"[SearchAggregator] CACHE HIT: {len(cached)} results for '{query}'")
                return [
                    {"title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source}
                    for r in cached
                ]
        
        # Get optimal provider order for this query
        if self.test_mode:
            # Test mode: Use DuckDuckGo first (free/unlimited, saves API tokens)
            provider_order = ["duckduckgo", "serper", "tavily", "exa", "searchapi", "google"]
            print(f"[SearchAggregator] TEST MODE: Using DuckDuckGo first")
        else:
            provider_order = self.router.get_provider_order(query)
        print(f"[SearchAggregator] Provider order: {provider_order}")
        
        # Try each provider in order
        for provider_name in provider_order:
            if provider_name not in self._providers:
                continue
                
            search_fn, has_key_fn = self._providers[provider_name]
            
            # Check if provider is configured and has quota
            if not has_key_fn():
                print(f"[SearchAggregator] Skipping {provider_name}: Not configured")
                continue
                
            if not self.quota.can_use(provider_name):
                print(f"[SearchAggregator] Skipping {provider_name}: Quota exhausted")
                continue
            
            try:
                print(f"[SearchAggregator] Attempting {provider_name} for: {query}")
                
                # Handle async vs sync methods
                if provider_name == "duckduckgo":
                    results = await search_fn(query)
                else:
                    results = search_fn(query)
                    
                if results:
                    self.quota.increment(provider_name)
                    print(f"[SearchAggregator] SUCCESS: {provider_name} returned {len(results)} results")
                    
                    # Store results in Sovereign Memory
                    if self._repository:
                        self._repository.store_results(query, query_type, results)
                    
                    return results
                    
            except Exception as e:
                print(f"[SearchAggregator] {provider_name} failed: {e}")
        
        print("[SearchAggregator] All providers exhausted, returning empty")
        return []


    def _search_google(self, query: str) -> List[Dict[str, Any]]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": 5
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": "google"
                })
        return results

    def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        client = TavilyClient(api_key=self.tavily_api_key)
        response = client.search(query, search_depth="basic", max_results=5)
        
        results = []
        if "results" in response:
            for item in response["results"]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("content"),
                    "source": "tavily"
                })
        return results

    def _search_serper(self, query: str) -> List[Dict[str, Any]]:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": 5})
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "organic" in data:
            for item in data["organic"]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": "serper"
                })
        return results

    def _search_exa(self, query: str) -> List[Dict[str, Any]]:
        exa = Exa(api_key=self.exa_api_key)
        response = exa.search_and_contents(
            query,
            num_results=5,
            use_autoprompt=True,
            text=True
        )
        
        results = []
        if response.results:
            for item in response.results:
                results.append({
                    "title": item.title,
                    "url": item.url,
                    # Exa returns 'text' content, we use first 200 chars as snippet
                    "snippet": item.text[:200] + "..." if item.text else "",
                    "source": "exa"
                })
        return results

    def _search_searchapi(self, query: str) -> List[Dict[str, Any]]:
        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "api_key": self.searchapi_api_key,
            "q": query,
            "engine": "google"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "organic_results" in data:
            for item in data["organic_results"]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": "searchapi"
                })
        return results

    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes DDG search via external process to avoid async loop conflicts.
        """
        import asyncio
        import json
        
        script_path = os.path.join(os.path.dirname(__file__), "ddg_search_tool.py")
        
        try:
            # Create a subprocess to run the script
            # We use python executable from env or just 'python'
            process = await asyncio.create_subprocess_exec(
                "python", script_path, query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"[SearchAggregator] DDG Script Error: {stderr.decode()}")
                return []
                
            output = stdout.decode().strip()
            if not output:
                return []
                
            return json.loads(output)
            
        except Exception as e:
            print(f"[SearchAggregator] DDG Subprocess Failed: {e}")
            return []
