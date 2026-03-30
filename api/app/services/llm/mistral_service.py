"""
Mistral AI Service
Integration dengan Mistral AI API
"""
from typing import Optional
from mistralai import Mistral

from api.app.services.llm.base import BaseLLMService
from api.app.utils.config import settings


class MistralService(BaseLLMService):
    """Mistral AI LLM service"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("Mistral API key is required")
        
        self.client = Mistral(api_key=self.api_key)
        self._model_name = settings.MISTRAL_MODEL
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """Generate response using Mistral AI"""
        try:
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
            
            response = self.client.chat.complete(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"Mistral AI generation error: {str(e)}")
