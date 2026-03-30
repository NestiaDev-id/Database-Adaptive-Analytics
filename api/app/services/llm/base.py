"""
Base LLM Service
Abstract base class untuk semua LLM providers
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMService(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt/message
            system_instruction: System instruction for the model
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used"""
        pass
