from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class VoiceQueryMetadata(BaseModel):
    session_id: Optional[str] = None
    farmer_id: Optional[str] = None
    state: Optional[str] = "Maharashtra"
    district: Optional[str] = None
    crop_name: Optional[str] = None
    soil_type: Optional[str] = None
    preferred_language: Optional[str] = None

class GroundedSource(BaseModel):
    title: str
    category: Optional[str] = "General Agronomy"
    excerpt: str
    relevance_score: Optional[float] = None

class VoiceQueryResponse(BaseModel):
    success: bool = True
    transcript: str = Field(description="Transcribed text from speech")
    detected_language: str = Field(description="Detected language code (hi, mr, te, etc.)")
    answer_text: str = Field(description="Grounded agricultural advice in vernacular")
    audio_base64: Optional[str] = Field(None, description="Synthesized voice audio in base64 format")
    audio_url: Optional[str] = Field(None, description="Direct URL to audio file if persisted")
    sources: List[GroundedSource] = Field(default_factory=list, description="Referenced ICAR/KVK documents")
    latency_breakdown_ms: Dict[str, float] = Field(default_factory=dict, description="STT, RAG, LLM, TTS latency metrics")
