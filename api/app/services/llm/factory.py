"""
LLM Factory
Factory pattern untuk memilih LLM provider berdasarkan model name
"""
from typing import Optional

from api.app.services.llm.base import BaseLLMService
from api.app.services.llm.groq_service import GroqService
from api.app.services.llm.gemini_service import GeminiService
from api.app.services.llm.openai_service import OpenAIService
from api.app.services.llm.deepseek_service import DeepSeekService
from api.app.services.llm.mistral_service import MistralService
from api.app.services.llm.cerebras_service import CerebrasService


class LLMFactory:
    """Factory class untuk membuat LLM service instances"""
    
    _providers = {
        "Gemini (Google)": GeminiService,
        "GPT-4 (OpenAI)": OpenAIService,
        "Groq (Llama 3)": GroqService,
        "DeepSeek": DeepSeekService,
        "Mistral AI": MistralService,
        "Cerebras": CerebrasService,
    }
    
    @classmethod
    def get_provider(cls, model_name: str, api_key: Optional[str] = None) -> BaseLLMService:
        """
        Get LLM provider instance based on model name
        
        Args:
            model_name: Name of the model (e.g., "Groq (Llama 3)")
            api_key: Optional API key override
            
        Returns:
            LLM service instance
            
        Raises:
            ValueError: If model name is not supported
        """
        if model_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown model: {model_name}. Available models: {available}")
        
        provider_class = cls._providers[model_name]
        
        # Handle masked input from frontend (treat "********" as None to trigger fallback)
        if api_key and all(c == '*' for c in api_key):
            api_key = None
            
        return provider_class(api_key=api_key)
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all available LLM providers"""
        return list(cls._providers.keys())

    @classmethod
    def get_provider_status(cls) -> dict[str, bool]:
        """
        Get status of availability for each provider based on API keys in settings.
        Returns:
            Dict[model_name, is_configured]
        """
        from api.app.utils.config import settings
        
        status = {}
        # Map model names to their setting keys
        # Note: This mapping needs to match the keys in _providers
        key_mapping = {
            "Gemini (Google)": settings.GOOGLE_API_KEY,
            "GPT-4 (OpenAI)": settings.OPENAI_API_KEY,
            "Groq (Llama 3)": settings.GROQ_API_KEY,
            "DeepSeek": settings.DEEPSEEK_API_KEY,
            "Mistral AI": settings.MISTRAL_API_KEY,
            "Cerebras": settings.CEREBRAS_API_KEY,
        }
        
        for model_name in cls._providers:
            # Check if key exists and is not empty
            api_key = key_mapping.get(model_name)
            status[model_name] = bool(api_key and api_key.strip())
            
        return status
