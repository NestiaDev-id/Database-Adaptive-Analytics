"""
OpenAI LLM Service
Integration dengan OpenAI GPT-4 API
"""
from typing import Optional
from openai import AsyncOpenAI

from api.app.services.llm.base import BaseLLMService
from api.app.utils.config import settings


class OpenAIService(BaseLLMService):
    """OpenAI GPT-4 API service"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.OPENAI_API_KEY)
        self.client = AsyncOpenAI(api_key=self.api_key)
        self._model = settings.OPENAI_MODEL
    
    @property
    def model_name(self) -> str:
        return f"OpenAI ({self._model})"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using OpenAI API"""
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
            return f"Error connecting to OpenAI API: {str(e)}"
