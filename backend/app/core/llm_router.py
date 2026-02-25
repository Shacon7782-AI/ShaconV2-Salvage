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
    Intelligent routing and Multi-Provider Waterfall failover for LLM requests.
    Utilizes LangChain's native .with_fallbacks() to gracefully handle 429/500 errors mid-inference.
    """
    
    @staticmethod
    def get_optimal_llm(model_override: Optional[str] = None, 
                          structured_schema: Optional[Dict[str, Any]] = None,
                          complexity: str = "MED"):
        """
        Returns a Chat model sequence resilient against rate limits and downtime.
        Tiers:
          1. Groq (Fastest / Llama 3 70B)
          2. Gemini Flash (Highest Free Limits)
          3. OpenRouter (Diverse Free Backup)
          4. Together AI (Cheap/Fast Llama 3 Backup)
          5. Local Ollama (Sovereign Failsafe)
        """
        google_api_key = os.getenv("GOOGLE_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        together_api_key = os.getenv("TOGETHER_API_KEY")

        models_pipeline = []

        # 1. Primary Attempt: Groq (Extreme Speed)
        if groq_api_key:
            llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_api_key, max_retries=1)
            models_pipeline.append(llm.with_structured_output(structured_schema) if structured_schema else llm)

        # 2. Secondary Attempt: Gemini Flash (Huge Free Tier)
        if google_api_key:
            target_model = model_override or "gemini-1.5-flash"
            llm = ChatGoogleGenerativeAI(model=target_model, google_api_key=google_api_key, max_retries=1)
            models_pipeline.append(llm.with_structured_output(structured_schema) if structured_schema else llm)

        # 3. Tertiary Attempt: OpenRouter (Diverse Free Backup)
        if openrouter_api_key and openrouter_api_key != "your_openrouter_api_key_here":
            llm = ChatOpenAI(
                model="meta-llama/llama-3.3-70b-instruct:free",
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=1
            )
            models_pipeline.append(llm.with_structured_output(structured_schema) if structured_schema else llm)

        # 4. Quaternary Attempt: Together AI
        if together_api_key and together_api_key != "your_together_api_key_here":
            llm = ChatOpenAI(
                model="meta-llama/Llama-3-8b-chat-hf",
                api_key=together_api_key,
                base_url="https://api.together.xyz/v1",
                max_retries=1
            )
            models_pipeline.append(llm.with_structured_output(structured_schema) if structured_schema else llm)

        # 5. Final Emergency Fallback: Sovereign Local (Ollama)
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        local_llm = ChatOllama(model="llama3", base_url=ollama_host)
        local_runnable = local_llm
        if structured_schema:
            try:
                 local_runnable = local_llm.with_structured_output(structured_schema)
            except Exception as e:
                 print(f"[ROUTER STARTUP] Ollama structured output disabled: {e}")
                 local_runnable = local_llm # fallback to raw

        models_pipeline.append(local_runnable)

        # Build the resilient fallback chain
        if not models_pipeline:
             return local_runnable
             
        primary = models_pipeline[0]
        if len(models_pipeline) > 1:
            return primary.with_fallbacks(models_pipeline[1:])
        return primary
