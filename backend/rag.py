import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.config import settings
from backend.language import detect_language, normalize_and_translate_query

logger = logging.getLogger(__name__)

# Global singleton embeddings and vector store cache
_embeddings_instance = None
_vectorstore_instance = None

def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Returns singleton instance of multilingual HuggingFace embeddings."""
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info(f"Loading multilingual embedding model: {settings.EMBEDDING_MODEL_NAME}")
        try:
            _embeddings_instance = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME,
                model_kwargs={"device": "cpu", "local_files_only": True},
                encode_kwargs={"normalize_embeddings": True}
            )
        except Exception:
            _embeddings_instance = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
    return _embeddings_instance

def build_unified_vectorstore(
    all_chunks: List[Dict[str, Any]],
    vectorstore_path: str
) -> FAISS:
    """
    Builds a unified FAISS vector store combining KCC records, ICAR/KVK PDF chunks,
    and National Agromet Bulletin chunks, and saves to disk.
    """
    os.makedirs(vectorstore_path, exist_ok=True)
    embeddings = get_embeddings_model()

    documents = []
    for r in all_chunks:
        text = r.get("searchable_doc") or r.get("answer") or r.get("question", "")
        doc = Document(
            page_content=text,
            metadata={
                "record_id": r.get("record_id", "REC-0000"),
                "question": r.get("question", ""),
                "answer": r.get("answer", ""),
                "crop": r.get("crop", "General"),
                "category": r.get("category", "General"),
                "source": r.get("source", "Agricultural Knowledge Base"),
                "filename": r.get("filename") or r.get("file_name", ""),
                "file_name": r.get("filename") or r.get("file_name", ""),
                "page_number": r.get("page_number"),
                "language": r.get("language", "en"),
                "location": r.get("location", "All India"),
                "date": r.get("date", "All Season"),
                "document_type": r.get("document_type", "advisory")
            }
        )
        documents.append(doc)

    logger.info(f"Generating embeddings and FAISS index for {len(documents):,} unified knowledge chunks...")
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(vectorstore_path)
    logger.info(f"Successfully saved unified FAISS vector store to {vectorstore_path}")

    global _vectorstore_instance
    _vectorstore_instance = vectorstore
    return vectorstore

def build_kcc_vectorstore(
    records: List[Dict[str, Any]],
    vectorstore_path: str
) -> FAISS:
    """Backward-compatible alias for build_unified_vectorstore."""
    return build_unified_vectorstore(records, vectorstore_path)

def load_kcc_vectorstore(vectorstore_path: str = None) -> Optional[FAISS]:
    """
    Loads FAISS vector store from local disk.
    """
    global _vectorstore_instance
    if _vectorstore_instance is not None:
        return _vectorstore_instance

    v_path = vectorstore_path or settings.VECTORSTORE_PATH
    if not os.path.exists(os.path.join(v_path, "index.faiss")):
        logger.warning(f"No FAISS index found at {v_path}. Run build_index.py first.")
        return None

    try:
        embeddings = get_embeddings_model()
        logger.info(f"Loading local FAISS index from {v_path}...")
        _vectorstore_instance = FAISS.load_local(
            v_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        return _vectorstore_instance
    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")
        return None

def retrieve_kcc_evidence(
    query: str,
    top_k: Optional[int] = None,
    language_code: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], str, bool, str]:
    """
    Performs vector similarity search across the UNIFIED knowledge base (KCC + ICAR/KVK PDFs).
    Uses dual query search (original multilingual query + English semantic normalization)
    to maximize cross-lingual retrieval accuracy from ICAR and KCC datasets.
    """
    k = top_k or settings.TOP_K or 6
    vectorstore = load_kcc_vectorstore()

    if vectorstore is None:
        return (
            [],
            "Low",
            False,
            "NO_VECTORSTORE: Knowledge base vector index not loaded. Please run `python scripts/build_index.py` first."
        )

    try:
        lang = language_code or detect_language(query)

        # 1. Search with original query
        results_orig = vectorstore.similarity_search_with_score(query, k=k)

        # 2. If Marathi or Hindi, also search with English translated query
        combined_results_dict = {}
        for doc, score in results_orig:
            key = doc.metadata.get("record_id") or doc.page_content[:60]
            combined_results_dict[key] = (doc, float(score))

        if lang in ["mr", "hi"]:
            eng_query = normalize_and_translate_query(query, language_code=lang)
            if eng_query and eng_query != query:
                results_trans = vectorstore.similarity_search_with_score(eng_query, k=k)
                for doc, score in results_trans:
                    key = doc.metadata.get("record_id") or doc.page_content[:60]
                    score_val = float(score)
                    if key not in combined_results_dict or score_val < combined_results_dict[key][1]:
                        combined_results_dict[key] = (doc, score_val)

        # Sort merged results by best distance score
        sorted_results = sorted(combined_results_dict.values(), key=lambda x: x[1])[:k]

    except Exception as e:
        logger.error(f"Error during vector search: {e}")
        return [], "Low", False, f"RETRIEVAL_ERROR: {str(e)}"

    if not sorted_results:
        return [], "Low", False, "NO_RECORDS_MATCHED"

    retrieved_records = []
    context_chunks = []
    best_score = float("inf")

    for idx, (doc, score_val) in enumerate(sorted_results):
        if score_val < best_score:
            best_score = score_val

        rec_id = doc.metadata.get("record_id", f"REC-{idx+1}")
        rec_q = doc.metadata.get("question", "")
        rec_a = doc.metadata.get("answer", doc.page_content)
        rec_crop = doc.metadata.get("crop", "General")
        rec_cat = doc.metadata.get("category", "General Agronomy")
        rec_src = doc.metadata.get("source", "Agricultural Advisory")
        filename = doc.metadata.get("filename") or doc.metadata.get("file_name", "")
        page_number = doc.metadata.get("page_number")
        rec_lang = doc.metadata.get("language", "en")
        rec_loc = doc.metadata.get("location", "All India")
        rec_date = doc.metadata.get("date", "All Season")
        doc_type = doc.metadata.get("document_type", "advisory")

        record_entry = {
            "record_id": rec_id,
            "question": rec_q,
            "answer": rec_a,
            "crop": rec_crop,
            "category": rec_cat,
            "source": rec_src,
            "filename": filename,
            "file_name": filename,
            "page_number": page_number,
            "language": rec_lang,
            "location": rec_loc,
            "date": rec_date,
            "document_type": doc_type,
            "similarity_distance": round(score_val, 4),
            "similarity_score": round(score_val, 4)
        }
        retrieved_records.append(record_entry)

        # Build detailed source chunk header
        page_info = f" | Page {page_number}" if page_number else ""
        doc_info = f" | Doc: {filename}" if filename else ""

        chunk_str = (
            f"[SOURCE {idx+1}: {rec_src}{doc_info}{page_info} | Crop: {rec_crop} | Category: {rec_cat} | Location: {rec_loc}]:\n"
            f"{rec_a}"
        )
        context_chunks.append(chunk_str)

    # Threshold for normalized L2 distance:
    # <= 0.85 -> High confidence
    # <= 1.28 -> Medium confidence (grounded match across languages/PDFs)
    # > 1.28 -> Low confidence
    if best_score <= 0.85:
        confidence = "High"
        is_grounded = True
    elif best_score <= settings.SIMILARITY_THRESHOLD:
        confidence = "Medium"
        is_grounded = True
    else:
        confidence = "Low"
        is_grounded = False

    context_str = "\n\n".join(context_chunks)
    return retrieved_records, confidence, is_grounded, context_str
