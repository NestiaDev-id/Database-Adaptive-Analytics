"""
Google Gemini LLM Service
Integration dengan Google Generative AI API
"""
from typing import Optional
import google.generativeai as genai

from api.app.services.llm.base import BaseLLMService
from api.app.utils.config import settings


class GeminiService(BaseLLMService):
    """Google Gemini API service"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.GOOGLE_API_KEY)
        genai.configure(api_key=self.api_key)
        self._model = settings.GEMINI_MODEL
    
    @property
    def model_name(self) -> str:
        return f"Gemini ({self._model})"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate response using Gemini API"""
        try:
            model = genai.GenerativeModel(
                model_name=self._model,
                system_instruction=system_instruction
            )
            
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or settings.DEFAULT_MAX_TOKENS,
            )
            
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text or ""
            
        except Exception as e:
            return f"Error connecting to Gemini API: {str(e)}"
