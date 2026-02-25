import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv

load_dotenv()

class SwarmLLMRouter:
    """
    Intelligent routing and failover for LLM requests.
    Standardizes on the Shacon-approved model strings.
    """
    
    @staticmethod
    def get_optimal_llm(model_override: Optional[str] = None, structured_schema: Optional[Dict[str, Any]] = None):
        """
        Returns a Chat model instance with optional structured output.
        Failover: Gemini (Primary) -> OpenAI (Secondary).
        """
        google_api_key = os.getenv("GOOGLE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Determine model
        model_name = model_override or "gemini-1.5-pro"
        
        # Primary: Google
        if google_api_key:
            try:
                llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key)
                if structured_schema:
                    return llm.with_structured_output(structured_schema)
                return llm
            except Exception as e:
                print(f"[ROUTER] Gemini fail: {e}")

        # Secondary: OpenAI
        if openai_api_key:
            try:
                model_name = "gpt-4o" if "pro" in model_name else "gpt-4o-mini"
                llm = ChatOpenAI(model=model_name, api_key=openai_api_key)
                if structured_schema:
                    return llm.with_structured_output(structured_schema)
                return llm
            except Exception as e:
                print(f"[ROUTER] OpenAI fail: {e}")

        # Final Sovereign Fallback: Local Ollama
        try:
            # Check for OLLAMA_HOST or default to localhost
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            # We assume llama3 is the default fast local model
            llm = ChatOllama(model="llama3", base_url=ollama_host)
            print(f"[ROUTER] Using Sovereign Local Model (Ollama: llama3)")
            # Note: Ollama structured output support varies by version/model
            # but we can at least return the LLM instance.
            return llm
        except Exception as e:
            print(f"[ROUTER] Ollama fail: {e}")

        print("[ROUTER] CRITICAL: No API keys configured or local providers failed.")
        return None
