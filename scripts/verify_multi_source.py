import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag import retrieve_kcc_evidence
from backend.llm import generate_grounded_answer

queries = [
    # 1. ICAR Kharif Advisory Query (English)
    ("What are the recommended sowing and irrigation practices for soybean in kharif season according to ICAR advisories?", "en"),
    # 2. Marathi query (Cotton Pink Bollworm & Pheromone Traps)
    ("कापसावरील गुलाबी बोंड अळीचे नियंत्रण कसे करावे?", "mr"),
    # 3. Hindi query (Wheat Irrigation CRI stage)
    ("गेहूं की फसल में पहली सिंचाई कब करनी चाहिए?", "hi"),
    # 4. Agromet Bulletin Query (Weather & Rainfall Advisory)
    ("National Agromet Advisory Bulletin weather forecast and rainfall advisory for farmers", "en")
]

print("=" * 80, flush=True)
print("🌾 KISANVANI MULTI-SOURCE RETRIEVAL VALIDATION", flush=True)
print("=" * 80, flush=True)

for q, lang in queries:
    print(f"\n==================================================================", flush=True)
    print(f"QUERY [{lang.upper()}]: {q}", flush=True)
    records, confidence, is_grounded, context_str = retrieve_kcc_evidence(q, top_k=5)
    print(f"Confidence: {confidence} | Grounded: {is_grounded} | Total Chunks: {len(records)}", flush=True)

    sources_found = set()
    for idx, r in enumerate(records, 1):
        src = r.get("source")
        doc = r.get("file_name")
        page = r.get("page_number")
        crop = r.get("crop")
        dist = r.get("similarity_distance")
        sources_found.add(src)
        print(f"  [{idx}] {src} | Crop: {crop} | Page: {page} | Doc: {doc} | Distance: {dist}", flush=True)
        print(f"      Text: {r.get('answer', '')[:130]}...", flush=True)

    answer = generate_grounded_answer(q, records, context_str, language_code=lang, confidence=confidence, is_grounded=is_grounded)
    print(f"\nAI ADVISORY ANSWER [{lang.upper()}]:\n{answer}", flush=True)
    print(f"Sources Used: {', '.join(sources_found)}", flush=True)
