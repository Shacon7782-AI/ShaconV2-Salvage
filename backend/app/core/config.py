import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    ShaconV2 Unified Settings.
    """
    PROJECT_NAME: str = "ShaconV2"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/shacon")
    
    # LLM
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Sovereign Memory
    MEMORY_TTL_HOURS: int = 24
    
    class Config:
        case_sensitive = True

settings = Settings()
