"""
DeepSeek LLM Service
Integration dengan DeepSeek API
"""
from typing import Optional
from openai import AsyncOpenAI

from api.app.services.llm.base import BaseLLMService
from api.app.utils.config import settings


class DeepSeekService(BaseLLMService):
    """DeepSeek API service (using OpenAI-compatible endpoint)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.DEEPSEEK_API_KEY)
        # DeepSeek uses OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.DEEPSEEK_API_BASE
        )
        self._model = settings.DEEPSEEK_MODEL
    
    @property
    def model_name(self) -> str:
        return f"DeepSeek ({self._model})"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using DeepSeek API"""
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
            return f"Error connecting to DeepSeek API: {str(e)}"
