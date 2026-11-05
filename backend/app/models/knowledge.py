from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class KnowledgeDocument(BaseModel):
    title: str
    category: str = Field(description="e.g., 'pest_and_disease', 'fertilizer', 'schemes'")
    crop: Optional[str] = Field(None, description="Applicable crop if specific")
    state: Optional[str] = Field(None, description="Applicable state if regional")
    content: str
    source_url: Optional[str] = None
    language: str = "en"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionStatus(BaseModel):
    total_documents: int
    total_chunks: int
    vector_dimension: int
    status: str = "success"
    message: str
