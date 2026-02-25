import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv

load_dotenv()

class SwarmLLMRouter:
    """
    Intelligent routing and failover for LLM requests.
    Standardizes on the Shacon-approved model strings.
    """
    
    @staticmethod
    def get_optimal_llm(model_override: Optional[str] = None, 
                          structured_schema: Optional[Dict[str, Any]] = None,
                          complexity: str = "MED"):
        """
        Returns a Chat model instance using the Economic Waterfall logic.
        Tiers:
          - LOW: Ollama (Llama 3)
          - MED: Groq (Llama 3 70B) or Gemini Flash
          - HIGH: Gemini 1.5 Pro
        """
        google_api_key = os.getenv("GOOGLE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")

        # 1. Tier: LOW (Sovereign/Local)
        if complexity == "LOW":
            try:
                ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                return ChatOllama(model="llama3", base_url=ollama_host)
            except Exception:
                pass # Fail up to MED if local fails

        # 2. Tier: MED (Fast/Cheap/Free)
        if complexity == "MED" or complexity == "LOW": # Fall up
            # Try Groq first for extreme speed
            if groq_api_key:
                try:
                    llm = ChatGroq(model="llama3-70b-8192", groq_api_key=groq_api_key)
                    if structured_schema:
                        return llm.with_structured_output(structured_schema)
                    return llm
                except Exception:
                    pass
            
            # Fallback to Gemini Flash (Free Tier)
            if google_api_key:
                try:
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=google_api_key)
                    if structured_schema:
                        return llm.with_structured_output(structured_schema)
                    return llm
                except Exception:
                    pass

        # 3. Tier: HIGH (The Architect)
        # Default to Gemini Pro
        target_model = model_override or "gemini-1.5-pro"
        if google_api_key:
            try:
                llm = ChatGoogleGenerativeAI(model=target_model, google_api_key=google_api_key)
                if structured_schema:
                    return llm.with_structured_output(structured_schema)
                return llm
            except Exception as e:
                print(f"[ROUTER] High Tier Failover (Gemini): {e}")

        # Final Emergency Fallback
        try:
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            return ChatOllama(model="llama3", base_url=ollama_host)
        except Exception:
            print("[ROUTER] CRITICAL: All tiers failed.")
            return None
