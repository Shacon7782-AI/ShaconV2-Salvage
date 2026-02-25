import asyncio
import os
from dotenv import load_dotenv
from app.core.llm_router import SwarmLLMRouter
from pydantic import BaseModel, Field

# Load environment carefully
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class AgentResponse(BaseModel):
    thoughts: str = Field(description="Internal reasoning")
    action: str = Field(description="Action to take")

async def test_waterfall():
    print("--- Testing Phase 10 Waterfall Failover ---")
    print(f"Loaded GROQ Key: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")
    print(f"Loaded OPENROUTER Key: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
    
    print("\n[TEST 1] Standard Routing (Should use Groq or Gemini depending on API Keys)")
    llm1 = SwarmLLMRouter.get_optimal_llm(structured_schema=AgentResponse)
    
    if hasattr(llm1, "invoke"):
        print(f"Primary Router selected: {type(llm1).__name__}")
        res = getattr(llm1, "invoke", None)("Explain water cycles in 1 sentence.")
        if res:
            print(f"Response: {res}")
    
    print("\n[TEST 2] Simulating Groq & Gemini Rate Limit (Forcing OpenRouter Fallback)")
    # Temporarily hide primary keys
    original_groq = os.environ.get("GROQ_API_KEY")
    original_gemini = os.environ.get("GOOGLE_API_KEY")
    
    os.environ["GROQ_API_KEY"] = ""
    os.environ["GOOGLE_API_KEY"] = ""
    
    llm2 = SwarmLLMRouter.get_optimal_llm(structured_schema=AgentResponse)
    print(f"Fallback Router selected: {type(llm2).__name__}")
    
    if hasattr(llm2, "invoke"):
         res = getattr(llm2, "invoke", None)("Explain fire in 1 sentence.")
         if res:
             print(f"Response: {res}")
             
    # Restore keys
    if original_groq: os.environ["GROQ_API_KEY"] = original_groq
    if original_gemini: os.environ["GOOGLE_API_KEY"] = original_gemini
    
if __name__ == "__main__":
    asyncio.run(test_waterfall())
