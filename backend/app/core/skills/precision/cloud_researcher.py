import asyncio
from typing import Dict, Any, List
from app.core.immudb_sidecar import immudb
from app.core import hardware
from ..base import BaseSkill, SkillMetadata, SkillResult
from app.core.agents.researcher.search_aggregator import SearchAggregator
from app.core.agents.researcher.scraper_tool import scrape_url
from app.core.llm_router import SwarmLLMRouter
from app.core.telemetry import Blackboard
from app.core.knowledge_graph import KnowledgeGraph
from app.core.agents.researcher.memory import save_knowledge
from app.core.memory.prompt_compressor import compressor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class CloudResearcherSkill(BaseSkill):
    """
    Cloud-Delegated Precision Skill for deep research.
    Uses free cloud APIs (Groq) and local scraping to minimize RAM usage.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="cloud_research",
            version="1.0.0",
            type="precision",
            description="Deep web research using cloud-delegated synthesis for 0-RAM footprint.",
            tags=["research", "cloud", "intelligence", "memory-safe"]
        )
        super().__init__(metadata)
        self.aggregator = SearchAggregator(test_mode=True)
        self.blackboard = Blackboard()

        self.knowledge_graph = KnowledgeGraph()
        
    async def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        query = inputs.get("query")
        if not query:
            return SkillResult(success=False, output="Missing query parameter", reward=-1.0)
            
        print(f"[SKILL] Executing Cloud Research: {query}")
        
        try:
            # 1. Search for URLs (DuckDuckGo fallback)
            print(f"[CLOUD RESEARCHER] Searching for: {query}")
            results = await self.aggregator.search(query)
            if not results:
                print(f"[CLOUD RESEARCHER] No results found for: {query}")
                immudb.log_operation(
                    "SKILL_FAILURE", 
                    {"skill": "cloud_researcher", "query": query, "reason": "no_results"}
                )
                return SkillResult(success=False, output="No search results found", reward=0.0)
            
            print(f"[CLOUD RESEARCHER] Found {len(results)} results. Scraping...")
            
            # 2. Scrape top 3 results for full content
            scraped_data = []
            for r in results[:3]:
                url = r.get("url")
                if url:
                    print(f"[SKILL] Scraping full content: {url}")
                    content = scrape_url(url)
                    if content:
                        scraped_data.append(content)
            
            # Audit the search and scrape phase
            immudb.log_operation(
                "SKILL_STEP", 
                {"skill": "cloud_researcher", "step": "search_and_scrape", "query": query, "results_count": len(scraped_data)}
            )
            
            if not scraped_data:
                return SkillResult(success=False, output="Failed to scrape deep content", reward=0.0)
            
            # 3. Compress Context with LLMLingua-2
            print(f"[SKILL] Compressing context for {query}...")
            compressed_context = compressor.compress(
                context=[data['content'] for data in scraped_data],
                instruction="Synthesize an expert answer for the given query.",
                question=query,
                target_token=1500
            )

            # 4. Synthesize with Groq (Cloud Brain)
            # Use MED tier for Groq Llama 3 70B
            llm = SwarmLLMRouter.get_optimal_llm(complexity="MED")
            
            prompt = ChatPromptTemplate.from_template(
                "You are an Elite Research AI. Based on the following expert-compressed context, provide a comprehensive expert synthesis for the query: '{query}'.\n\n"
                "CONTEXT:\n{context}\n\n"
                "Requirements:\n"
                "1. Focus on technical depth and actionable insights.\n"
                "2. Cite your sources clearly from the metadata if present.\n"
                "3. Use professional markdown formatting.\n"
                "4. Be concise but thorough."
            )
            
            chain = prompt | llm | StrOutputParser()
            synthesis = await chain.ainvoke({"query": query, "context": compressed_context})
            
            # Audit the synthesis phase
            immudb.log_operation(
                "SKILL_SUCCESS", 
                {"skill": "cloud_researcher", "query": query, "synthesis_preview": synthesis[:100]}
            )
            
            # 5. Save to Blackboard & Sovereign Memory
            self.blackboard.post_finding(
                "cloud-researcher", 
                f"Completed deep research synthesis for: {query}.\nSummary: {synthesis[:200]}...",
                related_mission_id=inputs.get("mission_id", "general")
            )
            
            # Save raw results for persistence
            await save_knowledge(query, results)
            
            return SkillResult(
                success=True,
                output=synthesis,
                reward=3.0,
                telemetry={
                    "sources_scraped": len(scraped_data),
                    "context_length": len(compressed_context)
                }
            )
            
        except Exception as e:
            print(f"[SKILL] Cloud Research failed: {e}")
            return SkillResult(
                success=False,
                output=str(e),
                reward=-2.0,
                telemetry={"error": str(e)}
            )

    def verify(self, result: SkillResult) -> bool:
        return result.success and len(result.output) > 300
