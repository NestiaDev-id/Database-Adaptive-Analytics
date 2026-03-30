"""
LLM Models
Pydantic schemas untuk LLM providers
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AIModel(str, Enum):
    """Supported AI models"""
    GEMINI = "Gemini (Google)"
    GPT4 = "GPT-4 (OpenAI)"
    GROQ = "Groq (Llama 3)"
    DEEPSEEK = "DeepSeek"


class LLMRequest(BaseModel):
    """Request model untuk LLM"""
    prompt: str = Field(..., description="User prompt")
    system_instruction: Optional[str] = Field(default=None, description="System instruction")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None)


class LLMResponse(BaseModel):
    """Response model dari LLM"""
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    usage: Optional[dict] = Field(default=None, description="Token usage info")
