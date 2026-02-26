import os
import json
import requests
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from duckduckgo_search import DDGS
from tavily import TavilyClient
from exa_py import Exa
from sqlalchemy.orm import Session
from .quota_manager import QuotaManager
from .provider_router import ProviderRouter
from app.core.immudb_sidecar import immudb

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

    async def stream_search(self, query: str, use_cache: bool = True):
        """
        Search using intelligent routing and yield results as they are found.
        """
        print(f"[SearchAggregator] Status: {self.quota.get_status()}")
        
        # 1. Check cache first
        if use_cache and self._repository:
            cached = self._repository.find_cached_results(query)
            if cached:
                print(f"[SearchAggregator] CACHE HIT: {len(cached)} results for '{query}'")
                for r in cached:
                    yield {"title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source}
                return

        # 2. Get query classification
        query_type, confidence = await self.router.classifier.classify(query)
        immudb.log_operation("SEARCH_QUERY", {"query": query, "type": query_type, "confidence": confidence})

        # 3. Get provider order
        if self.test_mode:
            providers = ["duckduckgo", "serper", "tavily", "exa", "searchapi", "google"]
        else:
            providers = await self.router.get_provider_order(query)
        
        count = 0
        for provider_name in providers:
            if provider_name in self._providers:
                search_method, availability_check = self._providers[provider_name]
                if not availability_check(): continue
                    
                print(f"[SearchAggregator] Querying {provider_name}...")
                results = await search_method(query)
                
                if results:
                    self.quota.increment(provider_name)
                    immudb.log_operation("SEARCH_PROVIDER_SUCCESS", {"provider": provider_name, "results_count": len(results)})
                    for r in results:
                        yield r
                        count += 1
                    if count >= 10: break

    async def search(self, query: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Backwards-compatible wrapper for stream_search.
        """
        results = []
        async for res in self.stream_search(query, use_cache):
            results.append(res)
            
        if not results: return []
            
        # Sovereign Intelligence: Rerank results with Groq
        final_results = await self.rerank_with_groq(query, results[:15])
        
        if self._repository and final_results:
            self._repository.store_results(query, "derived", final_results)
            
        return final_results

    async def rerank_with_groq(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Uses Groq (Extreme Speed) to rerank search results by relevance.
        """
        if not results:
            return []
            
        try:
            print(f"[SearchAggregator] Reranking {len(results)} results with GROQ...")
            llm = SwarmLLMRouter.get_optimal_llm(complexity="SIMPLE")
            
            # Prepare formatted list for LLM
            items = []
            for i, r in enumerate(results):
                items.append(f"ID: {i} | Title: {r.get('title')} | Snippet: {r.get('snippet', '')[:200]}")
            
            immudb.log_operation("GORG_INTEL_START", {"query": query, "step": "rerank", "count": len(results)})
            
            prompt = ChatPromptTemplate.from_template(
                "You are an Elite Search Reranker. Rank the following results by direct relevance to the query: '{query}'.\n"
                "RESULTS:\n{results_list}\n\n"
                "Return ONLY a JSON array of IDs in order of relevance, e.g., [2, 0, 5]. Max 5 IDs."
            )
            
            chain = prompt | llm | JsonOutputParser()
            ranked_ids = await chain.ainvoke({"query": query, "results_list": "\n".join(items)})
            
            immudb.log_operation("GORG_INTEL_SUCCESS", {"query": query, "step": "rerank", "ranked_ids": ranked_ids})
            
            # Map back to original objects
            reranked = []
            for rid in ranked_ids:
                if isinstance(rid, int) and 0 <= rid < len(results):
                    reranked.append(results[rid])
            
            # Fallback to original order if LLM failed to give enough results
            if not reranked:
                return results[:5]
                
            return reranked
        except Exception as e:
            print(f"[SearchAggregator] Groq reranking failed: {e}")
            return results[:5]


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
        Executes DDG search via executor to avoid async loop conflicts.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_search_duckduckgo, query)

    def _sync_search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        from duckduckgo_search import DDGS
        results = []
        try:
            print(f"[SearchAggregator] Attempting sync DDG search for: {query}")
            with DDGS() as ddgs:
                # Use the new DDGS search pattern
                # Note: max_results might be ignored in some versions, but we limit in loop
                ddg_gen = ddgs.text(query, max_results=5)
                if ddg_gen:
                    for i, r in enumerate(ddg_gen):
                        if i >= 5: break
                        results.append({
                            "title": r.get("title", "No Title"),
                            "url": r.get("href", r.get("link", "")),
                            "snippet": r.get("body", "No description available"),
                            "source": "duckduckgo"
                        })
            print(f"[SearchAggregator] DDG search returned {len(results)} results.")
        except Exception as e:
            print(f"[SearchAggregator] Sync DDG failed with error: {e}")
            # Optional: Add dummy result for testing if in test mode and everything fails
            if self.test_mode and not results:
                print("[SearchAggregator] TEST MODE: Providing synthetic result due to DDG failure.")
                results.append({
                    "title": f"Synthesis for {query}",
                    "url": "https://shacon.ai/synthetic",
                    "snippet": f"This is an automated system response because live search failed during integration testing for '{query}'.",
                    "source": "synthetic"
                })
        return results
