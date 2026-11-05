
import logging
from typing import List, Tuple, Optional

from app.rag.vector_store import FAISSVectorStoreManager
from app.models.voice import GroundedSource
from app.core.config import settings

logger = logging.getLogger(__name__)


CROP_KEYWORDS = {
    "Cotton": ["cotton", "कापूस", "कपास", "कापुस", "पत्ती"],
    "Wheat": ["wheat", "गहू", "गेहूं", "गेंहू", "कनक"],
    "Soybean": ["soybean", "सोयाबीन", "सोयाबिन", "सोया"],
    "Rice": ["rice", "paddy", "धान", "भात", "तांदूळ", "चावल"],
    "Sugarcane": ["sugarcane", "ऊस", "गन्ना"],
    "Tomato": ["tomato", "टोमॅटो", "टमाटर"],
    "Onion": ["onion", "कांदा", "प्याज"],
}


class RAGService:

    @classmethod
    def extract_crop_from_query(cls, query: str) -> Optional[str]:
        query_lower = query.lower()

        for crop_name, synonyms in CROP_KEYWORDS.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    return crop_name

        return None

    @classmethod
    def retrieve_grounded_context(
        cls,
        query: str,
        crop: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Tuple[str, List[GroundedSource], bool]:

        k = top_k or settings.TOP_K_RESULTS
        inferred_crop = crop or cls.extract_crop_from_query(query)

        docs = []

        # First attempt: crop-specific retrieval
        if inferred_crop:
            filter_dict = {"crop": inferred_crop}

            docs = FAISSVectorStoreManager.search_similar(
                query=query,
                top_k=k,
                filter_dict=filter_dict
            )

        # Fallback: search the complete FAISS index
        if not docs:
            logger.info(
                "Crop-specific retrieval returned no results. "
                "Trying global retrieval."
            )

            docs = FAISSVectorStoreManager.search_similar(
                query=query,
                top_k=k
            )

        if not docs:
            logger.warning(
                "No relevant documents retrieved for query: %s",
                query
            )

            return (
                "NO_TRUSTED_CONTEXT_FOUND: "
                "No verified agricultural advisory matches this query.",
                [],
                False
            )

        context_chunks = []
        sources = []
        best_score = float("inf")

        for idx, doc in enumerate(docs):

            metadata = doc.metadata or {}

            source_file = metadata.get(
                "source_file",
                "Agricultural Advisory Guide"
            )

            category = metadata.get(
                "category",
                "General Agronomy"
            )

            source_org = metadata.get(
                "source",
                "Agricultural Research Institute"
            )

            doc_crop = metadata.get("crop", "General")
            doc_state = metadata.get("state", "India")

            content = doc.page_content.strip()

            score = metadata.get("score")

            if score is not None:
                best_score = min(best_score, float(score))

            context_chunks.append(
                f"""
[Source {idx + 1}
File: {source_file}
Organization: {source_org}
Crop: {doc_crop}
Region: {doc_state}
Category: {category}]

{content}
"""
            )

            sources.append(
                GroundedSource(
                    title=f"{source_file} ({source_org})",
                    category=category,
                    excerpt=(
                        content[:220] + "..."
                        if len(content) > 220
                        else content
                    ),
                    relevance_score=(
                        round(float(score), 4)
                        if score is not None
                        else None
                    )
                )
            )

        # FAISS L2 distance: smaller score means closer match.
        is_grounded = (
            len(docs) > 0
            and best_score <= 1.25
        )

        context_string = "\n\n".join(context_chunks)

        logger.info(
            "Retrieved %d documents for query: %s",
            len(docs),
            query
        )

        return context_string, sources, is_grounded
