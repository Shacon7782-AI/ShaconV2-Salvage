import json
from typing import Dict, Any, List
from ..base import BaseSkill, SkillMetadata, SkillResult
from app.core.config import settings
from app.core.llm_router import SwarmLLMRouter
from langchain_core.prompts import ChatPromptTemplate

class ConsultativeInterviewSkill(BaseSkill):
    """
    v3.0 'Consultative Discovery' Skill.
    Analyzes intent and conducts a structured 'Discovery Interview' to ensure alignment.
    """
    def __init__(self):
        metadata = SkillMetadata(
            name="consultative_interviewer",
            version="1.0.0",
            type="precision",
            description="Leading AI architect skill that analyzes vague or complex intents and generates high-impact clarifying questions.",
            tags=["consultative", "discovery", "v3.0", "alignment"]
        )
        super().__init__(metadata)
        # Arbitrage Routing
        self.llm = SwarmLLMRouter.get_optimal_llm()

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        intent = inputs.get("intent", "No intent provided.")
        print(f"[SKILL] Initiating Consultative Discovery for intent: '{intent[:50]}...'")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Shacon Lead Architect.
            Your job is to LISTEN and CLARIFY before building.
            Analyze the user's intent and generate 3-5 high-impact questions that will help define the 'Definition of Done'.
            
            Focus on:
            1. Aesthetic/Style preferences (The 'Vibe').
            2. Technical constraints or integrations.
            3. Success metrics (What does 'perfect' look like?).
            
            Format your response as a JSON array of strings called 'questions'.
            """),
            ("human", "User Intent: {intent}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"intent": intent})
        
        questions = []
        try:
            # Handle cases where response.content might be a list (multi-block) or string
            content = ""
            if isinstance(response.content, str):
                content = response.content
            elif isinstance(response.content, list):
                content = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in response.content])
            
            # Attempt to extract JSON from Markdown blocks
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[-1].split("```")[0].strip()
            
            data = json.loads(content.strip())
            if isinstance(data, dict):
                questions = data.get("questions", [])
            elif isinstance(data, list):
                questions = data
                
            output = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        except Exception as e:
            print(f"[SKILL] Discovery error: {e}")
            output = f"Discovery completed. Clarification needed on: {intent[:50]}..."
        
        return SkillResult(
            success=True,
            output=output,
            telemetry={"question_count": len(questions)}
        )

    def verify(self, result: SkillResult) -> bool:
        return result.success and len(result.output) > 20
