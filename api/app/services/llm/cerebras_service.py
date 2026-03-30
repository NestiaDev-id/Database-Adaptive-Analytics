"""
Cerebras AI Service
Integration with Cerebras Cloud SDK
"""
from typing import Optional
from cerebras.cloud.sdk import Cerebras

from api.app.services.llm.base import BaseLLMService
from api.app.utils.config import settings


class CerebrasService(BaseLLMService):
    """Cerebras AI Service"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.CEREBRAS_API_KEY
        if not self.api_key:
            raise ValueError("Cerebras API key is required")
            
        self.client = Cerebras(api_key=self.api_key)
        self._model = settings.CEREBRAS_MODEL
    
    @property
    def model_name(self) -> str:
        return f"Cerebras ({self._model})"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """Generate response using Cerebras API"""
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
            # Note: The SDK is synchronous, but we're running in an async function.
            # Ideally this should be run in a thread executor if high concurrency is needed,
            # but for this scale it might be acceptable or we can optimize later.
            response = self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise RuntimeError(f"Cerebras API generation error: {str(e)}")
