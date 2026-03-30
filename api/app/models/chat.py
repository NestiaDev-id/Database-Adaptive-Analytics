"""
Chat Models
Pydantic schemas untuk chat functionality
"""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from api.app.models.database import DbContext


class Message(BaseModel):
    """Chat message model"""
    id: str = Field(..., description="Unique message ID")
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User message/question")
    dbContext: DbContext = Field(..., description="Database context including connection and schema")


class ChatResponse(BaseModel):
    """Response model for chat endpoint (LAM Architecture)"""
    id: str = Field(..., description="Response message ID")
    role: Literal["assistant"] = Field(default="assistant")
    content: str = Field(..., description="AI generated response")
    timestamp: datetime = Field(default_factory=datetime.now)
    model_used: Optional[str] = Field(default=None, description="Model yang digunakan")
    # LAM Architecture additions
    analysis_intent: Optional[dict] = Field(default=None, description="Parsed AnalysisIntent from LLM")
    query_result: Optional[dict] = Field(default=None, description="Query execution results")


class StreamChatResponse(BaseModel):
    """Streaming response model"""
    chunk: str
    done: bool = False
