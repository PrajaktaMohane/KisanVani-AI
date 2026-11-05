from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.voice import GroundedSource

class ChatMessage(BaseModel):
    role: str = Field(description="'farmer' or 'assistant'")
    content: str
    language: Optional[str] = "en"
    audio_url: Optional[str] = None
    sources: Optional[List[GroundedSource]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModel):
    id: Optional[str] = None
    session_id: str
    farmer_id: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackCreate(BaseModel):
    session_id: str
    message_index: int
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    is_helpful: bool
    comments: Optional[str] = None
    crop_name: Optional[str] = None
