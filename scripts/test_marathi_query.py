import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag import retrieve_kcc_evidence

query = "कापसावर गुलाबी बोंडअळीचा प्रादुर्भाव झाला आहे, काय उपाय करावा?"

print("=" * 80)
print(f"🌾 DIRECT RETRIEVAL TEST (WITHOUT LLM)")
print(f"QUERY: {query}")
print("=" * 80)

records, confidence, is_grounded, context_str = retrieve_kcc_evidence(query, top_k=10)

print(f"\nTotal Retrieved Chunks: {len(records)}")
print(f"Overall Confidence: {confidence}")
print(f"Is Grounded: {is_grounded}\n")

for i, r in enumerate(records, 1):
    source = r.get("source", "N/A")
    filename = r.get("filename") or r.get("file_name", "N/A")
    page = r.get("page_number")
    page_str = str(page) if page is not None else "N/A"
    score = r.get("similarity_score", r.get("similarity_distance", "N/A"))
    answer_text = r.get("answer", "")
    snippet = answer_text[:300].strip()

    print(f"--- [CHUNK {i}] ---")
    print(f"Source:           {source}")
    print(f"Filename:         {filename}")
    print(f"Page:             {page_str}")
    print(f"Similarity Score: {score}")
    print(f"Content (First 300 chars):")
    print(f"{snippet}")
    print("-" * 60)
