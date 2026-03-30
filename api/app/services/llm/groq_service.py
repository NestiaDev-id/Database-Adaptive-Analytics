"""
Groq LLM Service
Integration dengan Groq API (Llama 3)
"""
from typing import Optional
from groq import AsyncGroq

from api.app.services.llm.base import BaseLLMService
from api.app.utils.config import settings


class GroqService(BaseLLMService):
    """Groq API service for Llama 3"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.GROQ_API_KEY)
        self.client = AsyncGroq(api_key=self.api_key)
        self._model = settings.GROQ_MODEL
    
    @property
    def model_name(self) -> str:
        return f"Groq ({self._model})"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using Groq API"""
        messages = []
        
        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or settings.DEFAULT_MAX_TOKENS,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            return f"Error connecting to Groq API: {str(e)}"
