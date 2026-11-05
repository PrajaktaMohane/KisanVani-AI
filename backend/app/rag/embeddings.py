import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingManager:
    _instance = None

    @classmethod
    def get_embedding_model(cls):
        if cls._instance is None:
            logger.info(f"Loading multilingual embedding model: {settings.EMBEDDING_MODEL_NAME}")
            cls._instance = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info("Embedding model loaded successfully.")
        return cls._instance
