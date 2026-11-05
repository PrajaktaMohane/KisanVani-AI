import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import sys
import time
import shutil
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from backend.data_loader import (
    clean_and_process_kcc_data,
    load_processed_data,
    discover_all_pdfs,
    extract_and_chunk_pdf
)
from backend.rag import build_unified_vectorstore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    t_start = time.time()
    print("=" * 80)
    print("🌾 KISANVANI MULTI-SOURCE VECTOR KNOWLEDGE BASE BUILDER")
    print("=" * 80)

    # 1. Locate Raw KCC Dataset
    kcc_csv = settings.ORIGINAL_DATA_PATH
    if not os.path.exists(kcc_csv):
        kcc_csv = os.path.join(settings.BASE_DIR, "data", "kcc_dataset.csv")
    if not os.path.exists(kcc_csv):
        kcc_csv = os.path.join(settings.BASE_DIR, "data", "original", "kcc_dataset.csv")

    if not os.path.exists(kcc_csv):
        print(f"❌ Error: KCC dataset not found at {kcc_csv}")
        sys.exit(1)

    # 2. Locate PDF Files
    search_dirs = [
        os.path.join(settings.BASE_DIR, "data"),
        os.path.join(settings.BASE_DIR, "data", "raw_documents"),
        os.path.join(settings.BASE_DIR, "backend", "data", "raw_documents")
    ]
    discovered_pdfs = discover_all_pdfs(search_dirs)

    print(f"\n📂 Source Verification:")
    print(f"  • KCC Raw Dataset:   {kcc_csv} (Exists: True)")
    print(f"  • Discovered PDFs:   {len(discovered_pdfs)} files")
    for p in discovered_pdfs:
        print(f"      - {os.path.basename(p)} ({os.path.getsize(p) / (1024*1024):.2f} MB)")

    # 3. Clean and Ingest KCC Dataset
    print("\n🧹 Ingesting and Cleaning Kisan Call Centre (KCC) Data...")
    kcc_stats = clean_and_process_kcc_data(
        input_csv_path=kcc_csv,
        output_csv_path=settings.PROCESSED_DATA_PATH,
        output_jsonl_path=settings.PROCESSED_JSONL_PATH,
        max_records=10000
    )
    kcc_records = load_processed_data(settings.PROCESSED_DATA_PATH)
    kcc_chunk_count = len(kcc_records)
    print(f"  ✓ Processed KCC records: {kcc_chunk_count:,}")

    # 4. Extract and Chunk All PDFs
    print("\n📄 Extracting and Chunking PDF Advisory Documents...")
    all_pdf_chunks = []
    icar_chunks_count = 0
    second_pdf_chunks_count = 0
    other_pdf_chunks_count = 0

    for pdf_path in discovered_pdfs:
        fname = os.path.basename(pdf_path)
        fname_lower = fname.lower()
        chunks = extract_and_chunk_pdf(pdf_path, chunk_size=700, chunk_overlap=120)
        print(f"  ✓ {fname}: {len(chunks):,} chunks extracted")
        
        if "icar" in fname_lower or "kharif" in fname_lower:
            icar_chunks_count += len(chunks)
        elif "bulletin" in fname_lower or "national" in fname_lower or "imd" in fname_lower:
            second_pdf_chunks_count += len(chunks)
        else:
            other_pdf_chunks_count += len(chunks)
            
        all_pdf_chunks.extend(chunks)

    # 5. Combine All Chunks
    unified_knowledge_chunks = kcc_records + all_pdf_chunks
    total_chunks = len(unified_knowledge_chunks)

    # 6. Delete old stale FAISS index before rebuilding
    vectorstore_path = settings.VECTORSTORE_PATH
    if os.path.exists(vectorstore_path):
        print(f"\n🗑️  Removing old vector store at: {vectorstore_path}")
        shutil.rmtree(vectorstore_path)
    os.makedirs(vectorstore_path, exist_ok=True)

    # 7. Generate Multilingual Embeddings and Save Vector Store
    print(f"\n🚀 Embedding {total_chunks:,} unified chunks with {settings.EMBEDDING_MODEL_NAME}...")
    t_embed_start = time.time()
    vectorstore = build_unified_vectorstore(
        all_chunks=unified_knowledge_chunks,
        vectorstore_path=vectorstore_path
    )
    t_embed_end = time.time()

    t_total = round(time.time() - t_start, 2)
    t_embed = round(t_embed_end - t_embed_start, 2)

    print("\n" + "=" * 80)
    print("📊 INDEXING RESULTS")
    print("=" * 80)
    print(f"KCC chunks: {kcc_chunk_count:,}")
    print(f"ICAR chunks: {icar_chunks_count:,}")
    print(f"Second PDF chunks: {second_pdf_chunks_count:,}")
    if other_pdf_chunks_count > 0:
        print(f"Other PDF chunks: {other_pdf_chunks_count:,}")
    print(f"Total chunks: {total_chunks:,}")
    print("=" * 80)
    print(f"Vector Store Path:    {vectorstore_path}")
    print(f"FAISS Total Vectors:  {vectorstore.index.ntotal:,}")
    print(f"Embedding Time:       {t_embed}s")
    print(f"Total Build Time:     {t_total}s")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
