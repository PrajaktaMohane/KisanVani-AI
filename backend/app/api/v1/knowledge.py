import os
import glob
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, status
from app.models.knowledge import IngestionStatus
from app.rag.ingest import run_ingestion
from app.rag.vector_store import FAISSVectorStoreManager
from app.services.rag_service import RAGService
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_knowledge_base_status():
    """
    Returns statistics on raw document counts across ICAR, KVK, KCC, and IMD,
    along with FAISS vector index status.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    raw_dir = os.path.join(base_dir, "data", "raw_documents")
    index_dir = FAISSVectorStoreManager.get_index_path()

    categories = ["icar", "kvk", "kisan_call_centre", "imd_agromet", "other_verified_sources"]
    counts = {}
    total_docs = 0

    for cat in categories:
        cat_path = os.path.join(raw_dir, cat)
        files = glob.glob(os.path.join(cat_path, "*.*"))
        # Exclude README files from doc count
        doc_files = [f for f in files if not os.path.basename(f).lower().startswith("readme")]
        counts[cat] = len(doc_files)
        total_docs += len(doc_files)

    index_exists = os.path.exists(os.path.join(index_dir, "index.faiss"))

    return {
        "total_documents": total_docs,
        "category_breakdown": counts,
        "faiss_index_exists": index_exists,
        "index_path": index_dir,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "similarity_threshold": settings.SIMILARITY_THRESHOLD
    }

@router.post("/upload")
async def kvk_expert_upload(
    file: UploadFile = File(..., description="PDF or TXT agricultural advisory"),
    crop: str = Form(..., description="Target crop e.g. Cotton, Wheat, Soybean"),
    category: str = Form(default="Pest and Disease"),
    state: str = Form(default="Maharashtra"),
    language: str = Form(default="mr"),
    source_org: str = Form(default="Krishi Vigyan Kendra (KVK)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    KVK Expert portal: Upload verified agricultural advisory with metadata,
    which saves to data/raw_documents/kvk/ and triggers automatic vector store re-indexing.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    kvk_dir = os.path.join(base_dir, "data", "raw_documents", "kvk")
    os.makedirs(kvk_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".txt", ".pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt and .pdf documents are supported."
        )

    file_bytes = await file.read()
    save_filename = f"kvk_{crop.lower()}_{language}_{os.path.basename(file.filename)}"
    target_path = os.path.join(kvk_dir, save_filename)

    # If text file, prepend metadata header for reliable parsing
    if file_ext == ".txt":
        try:
            content_str = file_bytes.decode("utf-8")
            header = f"Title: {os.path.splitext(file.filename)[0]}\nSource: {source_org}\nCrop: {crop}\nCategory: {category}\nState: {state}\nLanguage: {language}\n\n"
            final_content = header + content_str
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(final_content)
        except UnicodeDecodeError:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
    else:
        with open(target_path, "wb") as f:
            f.write(file_bytes)

    logger.info(f"KVK Expert uploaded {save_filename}. Scheduling background re-ingestion...")
    background_tasks.add_task(run_ingestion)

    return {
        "status": "success",
        "message": f"Advisory '{file.filename}' uploaded successfully. Vector index is updating in the background.",
        "saved_path": target_path,
        "metadata": {
            "crop": crop,
            "category": category,
            "state": state,
            "language": language,
            "source": source_org
        }
    }

@router.post("/ingest", response_model=IngestionStatus)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Triggers full re-indexing and vector database embedding of agricultural documents.
    """
    background_tasks.add_task(run_ingestion)
    return IngestionStatus(
        total_documents=0,
        total_chunks=0,
        vector_dimension=384,
        status="processing",
        message="Knowledge base ingestion pipeline started in background."
    )

@router.get("/search")
async def search_knowledge_base(query: str, crop: Optional[str] = None):
    """
    RAG Explorer endpoint for the Admin Dashboard to test semantic search similarity directly.
    """
    context_str, sources, is_grounded = RAGService.retrieve_grounded_context(query=query, crop=crop)
    return {
        "query": query,
        "crop": crop,
        "is_grounded": is_grounded,
        "sources": sources,
        "retrieved_context": context_str
    }
