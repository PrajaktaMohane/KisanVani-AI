import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    print("1. Loading embeddings...", flush=True)
    from backend.rag import get_embeddings_model
    embeddings = get_embeddings_model()
    print("2. Embeddings loaded successfully.", flush=True)

    print("3. Loading FAISS index from disk...", flush=True)
    from langchain_community.vectorstores import FAISS
    vs = FAISS.load_local("data/vectorstore/kcc_faiss_index", embeddings, allow_dangerous_deserialization=True)
    print(f"4. FAISS loaded successfully! Total vectors: {vs.index.ntotal:,}", flush=True)

    print("5. Performing search for 'soybean sowing kharif'...", flush=True)
    results = vs.similarity_search_with_score("soybean sowing kharif", k=5)
    print(f"6. Search complete! Found {len(results)} results:", flush=True)
    for doc, score in results:
        print(f"   -> Score: {score:.4f} | Source: {doc.metadata.get('source')} | Doc: {doc.metadata.get('file_name')} | Page: {doc.metadata.get('page_number')}", flush=True)
        print(f"      Content: {doc.page_content[:150]}...\n", flush=True)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
