import os
from typing import List, Union, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    """
    APP_NAME: str = "KisanVani AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"

    # MongoDB Settings
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "kisanvani_db"

    # Speech to Text (STT) Settings
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"  # 'cuda' or 'cpu'

    # Text to Speech (TTS) Settings
    TTS_ENGINE: str = "gtts"  # 'google-cloud', 'gtts', 'gemini-audio'
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # RAG & FAISS Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    # FAISS_INDEX_PATH: str = "data/vector_indices/agri_faiss_index"
    FAISS_INDEX_PATH: str = "data/vectorstore/kcc_faiss_index"
    TOP_K_RESULTS: int = 4
    SIMILARITY_THRESHOLD: float = 0.55  # Minimum similarity threshold for RAG grounding

    # Storage for Temp Audio
    AUDIO_TEMP_DIR: str = "data/audio_temp"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_service_status(self) -> Dict[str, Any]:
        """
        Returns sanitized configuration and service availability without leaking secrets.
        """
        return {
            "app_name": self.APP_NAME,
            "gemini_api_configured": bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY) > 5),
            "gemini_model": self.GEMINI_MODEL_NAME,
            "mongodb_configured": bool(self.MONGO_URI),
            "stt_engine": "whisper / faster-whisper",
            "whisper_model_size": self.WHISPER_MODEL_SIZE,
            "tts_engine": self.TTS_ENGINE,
            "embedding_model": self.EMBEDDING_MODEL_NAME,
            "similarity_threshold": self.SIMILARITY_THRESHOLD,
        }

settings = Settings()
