
import os
import logging
from typing import List, Dict, Any, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class FAISSVectorStoreManager:
    _vector_store: Optional[FAISS] = None

    @classmethod
    def get_index_path(cls) -> str:
        # Use the project root as the base directory
        project_root = os.getcwd()

        index_path = os.path.join(
            project_root,
            settings.FAISS_INDEX_PATH
        )

        return os.path.normpath(index_path)

    @classmethod
    def load_vector_store(cls) -> Optional[FAISS]:

        index_dir = cls.get_index_path()

        if cls._vector_store is not None:
            return cls._vector_store

        faiss_file = os.path.join(index_dir, "index.faiss")
        pickle_file = os.path.join(index_dir, "index.pkl")

        if os.path.isfile(faiss_file) and os.path.isfile(pickle_file):

            try:
                embeddings = EmbeddingManager.get_embedding_model()

                logger.info(
                    f"Loading existing FAISS index from {index_dir}..."
                )

                cls._vector_store = FAISS.load_local(
                    folder_path=index_dir,
                    embeddings=embeddings,
                    allow_dangerous_deserialization=True
                )

                logger.info("FAISS index loaded successfully.")

                return cls._vector_store

            except Exception as e:
                logger.exception(
                    f"Failed to load FAISS index: {e}"
                )
                return None

        else:
            logger.warning(
                f"FAISS index files not found at {index_dir}. "
                "Vector store needs ingestion."
            )
            return None

    @classmethod
    def save_vector_store(cls, vector_store: FAISS):

        index_dir = cls.get_index_path()

        os.makedirs(index_dir, exist_ok=True)

        vector_store.save_local(index_dir)

        cls._vector_store = vector_store

        logger.info(
            f"Saved FAISS index to {index_dir}"
        )

    @classmethod
    def search_similar(
        cls,
        query: str,
        top_k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:

        store = cls.load_vector_store()

        if store is None:
            logger.warning(
                "FAISS store not initialized; returning empty results."
            )
            return []

        try:
            results = store.similarity_search_with_score(
                query,
                k=top_k,
                filter=filter_dict
            )

            documents = []

            for doc, score in results:
                doc.metadata["score"] = float(score)
                documents.append(doc)

            return documents

        except Exception as e:
            logger.exception(
                f"FAISS search failed: {e}"
            )
            return []
