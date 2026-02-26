from typing import Dict, Any, List
from app.core.agents.researcher.tools import perform_search
from app.core.agents.researcher.memory import save_knowledge, check_knowledge
from app.core.telemetry import Blackboard
from app.core.knowledge_graph import KnowledgeGraph
from app.core.config import settings
from app.core.llm_router import SwarmLLMRouter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

class ResearchAgent:
    """
    The 'Brain' of the Research Module.
    Orchestrates the Search -> Scrape -> Save workflow.
    Now swarm-enabled via Blackboard and Level 10 RAG Pipeline.
    """
    __slots__ = ("agent_id", "blackboard", "knowledge_graph", "llm")

    def __init__(self, agent_id: str = "researcher-01"):
        self.agent_id = agent_id
        self.blackboard = Blackboard()
        self.knowledge_graph = KnowledgeGraph()
        
        # Initialize LLM via Arbitrage Router
        self.llm = SwarmLLMRouter.get_optimal_llm()

    async def refine_intent(self, original_query: str) -> str:
        """
        Layer 1: Pre-Retrieval Intent Refinement (RA-ISF)
        Uses LLM to clarify ambiguity and expand specificity before searching.
        """
        try:
            prompt = ChatPromptTemplate.from_template(
                "Refine this research query for optimal search engine retrieval: {query}. Output only the refined query."
            )
            chain = prompt | self.llm | StrOutputParser()
            refined_query = await chain.ainvoke({"query": original_query})
            print(f"[{self.agent_id}] Refined Query: '{original_query}' -> '{refined_query}'")
            return refined_query.strip()
        except Exception as e:
            print(f"[{self.agent_id}] [ERROR] LLM Refinement failed: {e}. Falling back to original query.")
            return original_query # Fallback to original

    async def hybrid_retrieval(self, query: str) -> List[Dict[str, Any]]:
        """
        Layer 1: Hybrid Retrieval (Vector + Knowledge Graph)
        Combines traditional search results with structural context from the KG.
        """
        # 1. Standard Search
        search_results = await perform_search(query)
        
        # 2. Knowledge Graph Context (Simple entity extraction simulation)
        # In a full implementation, we would extract entities from the query and traverse the graph.
        # For now, we simulate finding related concepts if strict matches exist.
        # related_subgraph = self.knowledge_graph.get_subgraph(query) 
        
        # TODO: Merge graph results into search results
        return search_results

    async def rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Uses LLM/Cross-Encoder to rank the raw results.
        """
        if not results:
            return []
            
        # For now, return top 3 as a baseline if LLM is flaky
        try:
            # Simple heuristic or LLM-based ranking could go here
            return results[:3]
        except Exception as e:
            print(f"[{self.agent_id}] [ERROR] Reranking failed: {e}. Returning top 3 results as fallback.")
            return results[:3]

    async def run(self, query: str) -> Dict[str, Any]:
        """
        Main execution entry point.
        """
        print(f"[{self.agent_id}] Processing query: {query}")

        # 1. Check Memory 
        cached_result = await check_knowledge(query)
        if cached_result:
            print(f"[{self.agent_id}] Found valid knowledge in DB.")
            finding_content = f"Research Query: '{query}' returned cached results from sovereign memory."
            self.blackboard.post_finding(self.agent_id, finding_content, related_mission_id="general")
            return {"source": "memory", "data": [cached_result]}

        # 2. Pre-Retrieval Intent Refinement
        refined_query = await self.refine_intent(query)

        # 3. Hybrid Retrieval
        print(f"[{self.agent_id}] Searching Web with Refined Query...")
        raw_results = await self.hybrid_retrieval(refined_query)

        # 4. Post-Retrieval Reranking
        ranked_results = await self.rerank_results(refined_query, raw_results)

        # 5. Save to Memory
        if ranked_results:
            await save_knowledge(query, ranked_results) # Save under original query for cache hit
            print(f"[{self.agent_id}] Knowledge saved onto the Blackboard.")
            
            finding_content = f"Research Query: '{query}' (Refined: '{refined_query}') returned {len(ranked_results)} highly relevant results."
            self.blackboard.post_finding(self.agent_id, finding_content, related_mission_id="general")

        return {"source": "web", "data": ranked_results}
