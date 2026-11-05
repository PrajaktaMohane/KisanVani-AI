import os
import re
import glob
import logging
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from app.rag.embeddings import EmbeddingManager
from app.rag.text_splitter import get_agricultural_text_splitter
from app.rag.vector_store import FAISSVectorStoreManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_metadata_from_text(content: str, default_source_file: str, default_category: str) -> Dict[str, Any]:
    """
    Extracts structured agricultural metadata from document headers if present.
    """
    meta: Dict[str, Any] = {
        "source_file": default_source_file,
        "category": default_category,
        "crop": "General",
        "source": "Verified Agricultural Source",
        "language": "en",
        "pest_disease": "None",
        "state": "Pan-India",
    }

    # Extract Crop
    crop_match = re.search(r"(?:Crop|फसल|पीक)\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
    if crop_match:
        meta["crop"] = crop_match.group(1).strip()

    # Extract Source
    source_match = re.search(r"(?:Source|स्रोत)\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
    if source_match:
        meta["source"] = source_match.group(1).strip()

    # Extract Category
    cat_match = re.search(r"(?:Category|वर्ग|श्रेणी)\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
    if cat_match:
        meta["category"] = cat_match.group(1).strip()

    # Extract Language
    lang_match = re.search(r"(?:Language|भाषा)\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
    if lang_match:
        meta["language"] = lang_match.group(1).strip()
    else:
        # Infer language from devanagari characters
        if re.search(r"[\u0900-\u097F]", content[:300]):
            meta["language"] = "hi" if "है" in content or "कीजिए" in content else "mr"

    # Extract State/Region
    state_match = re.search(r"(?:State|Region|Agro-climatic Zones|राज्य)\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
    if state_match:
        meta["state"] = state_match.group(1).strip()

    # Extract Pest/Disease
    pest_match = re.search(r"(?:Pest|Disease|Pests|रोग|कीड|सुंडी)\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
    if pest_match:
        meta["pest_disease"] = pest_match.group(1).strip()

    return meta

def load_documents_from_directory(data_dir: str) -> List[Document]:
    documents = []
    text_files = glob.glob(os.path.join(data_dir, "**/*.txt"), recursive=True)
    pdf_files = glob.glob(os.path.join(data_dir, "**/*.pdf"), recursive=True)

    for file_path in text_files:
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                folder_name = os.path.basename(os.path.dirname(file_path))
                extracted_meta = extract_metadata_from_text(
                    doc.page_content,
                    default_source_file=os.path.basename(file_path),
                    default_category=folder_name
                )
                doc.metadata.update(extracted_meta)
            documents.extend(docs)
            logger.info(f"Loaded text doc: {file_path} (Crop: {extracted_meta.get('crop')}, Source: {extracted_meta.get('source')})")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")

    for file_path in pdf_files:
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            for doc in docs:
                folder_name = os.path.basename(os.path.dirname(file_path))
                extracted_meta = extract_metadata_from_text(
                    doc.page_content,
                    default_source_file=os.path.basename(file_path),
                    default_category=folder_name
                )
                doc.metadata.update(extracted_meta)
            documents.extend(docs)
            logger.info(f"Loaded PDF doc: {file_path}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")

    return documents

def run_ingestion() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data", "raw_documents")

    logger.info(f"Starting agricultural knowledge base ingestion from {data_dir}...")
    raw_docs = load_documents_from_directory(data_dir)

    if not raw_docs:
        logger.warning("No documents found to ingest.")
        return {"status": "empty", "total_docs": 0, "total_chunks": 0}

    logger.info(f"Loaded {len(raw_docs)} raw documents. Splitting into chunks...")
    splitter = get_agricultural_text_splitter()
    chunked_docs = splitter.split_documents(raw_docs)
    logger.info(f"Generated {len(chunked_docs)} chunks.")

    embeddings = EmbeddingManager.get_embedding_model()
    logger.info("Building FAISS vector index...")
    vector_store = FAISS.from_documents(chunked_docs, embeddings)

    FAISSVectorStoreManager.save_vector_store(vector_store)
    logger.info("Ingestion completed successfully!")
    return {
        "status": "success",
        "total_docs": len(raw_docs),
        "total_chunks": len(chunked_docs),
        "index_path": FAISSVectorStoreManager.get_index_path()
    }

if __name__ == "__main__":
    run_ingestion()
