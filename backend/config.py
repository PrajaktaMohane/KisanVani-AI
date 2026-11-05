import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
from typing import List, Union, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for KisanVani KCC Agri-Advisory RAG System.
    """
    APP_NAME: str = "Voice-First Multilingual Agri-Advisory"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8501", "*"]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Google Gemini / LLM Settings
    LLM_API_KEY: str = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")

    # Dataset Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ORIGINAL_DATA_PATH: str = os.path.join(BASE_DIR, "data", "original", "kcc_dataset.csv")
    PROCESSED_DATA_PATH: str = os.path.join(BASE_DIR, "data", "processed", "kcc_cleaned.csv")
    PROCESSED_JSONL_PATH: str = os.path.join(BASE_DIR, "data", "processed", "kcc_cleaned.jsonl")
    VECTORSTORE_PATH: str = os.path.join(BASE_DIR, "data", "vectorstore", "kcc_faiss_index")
    SQLITE_DB_PATH: str = os.path.join(BASE_DIR, "data", "kisanvani.db")

    # Audio Directories
    AUDIO_INPUT_DIR: str = os.path.join(BASE_DIR, "data", "audio", "input")
    AUDIO_OUTPUT_DIR: str = os.path.join(BASE_DIR, "data", "audio", "output")

    # Embedding & RAG
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    TOP_K: int = int(os.getenv("TOP_K", "4"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "1.25"))

    # Speech to Text & TTS Settings
    WHISPER_MODEL_SIZE: str = "base"
    TTS_ENGINE: str = "gtts"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
