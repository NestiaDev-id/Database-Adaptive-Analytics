"""
Configuration Settings
Environment variables dan settings untuk aplikasi
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "DB Analyst AI"
    DEBUG: bool = True
    
    # API Keys for LLM Providers
    GROQ_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    CEREBRAS_API_KEY: Optional[str] = None
    
    # Database Fallback Settings (Optional)
    DB_HOST: str = ""
    DB_PORT: int = 0
    DB_USER: str = ""
    DB_PASS: str = ""
    DB_NAME: str = ""
    DB_TYPE: str = "PostgreSQL" # Default fallback type
    DB_URI: Optional[str] = None # Full connection string for Cloud (Supabase, Atlas, etc.)
    
    # Default LLM Settings
    DEFAULT_MODEL: str = "Groq (Llama 3)"
    DEFAULT_TEMPERATURE: float = 0.2
    DEFAULT_MAX_TOKENS: int = 4096
    
    # Groq specific
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # Gemini specific
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # OpenAI specific
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # DeepSeek specific
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    
    # Mistral specific
    MISTRAL_MODEL: str = "mistral-large-latest"
    
    # Cerebras specific
    CEREBRAS_MODEL: str = "llama-3.3-70b"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
