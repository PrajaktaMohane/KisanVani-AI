import sys
import os
import base64
from fastapi.testclient import TestClient

from backend.main import app
from backend.rag import load_kcc_vectorstore, get_embeddings_model

client = TestClient(app)
get_embeddings_model()
load_kcc_vectorstore()

test_cases = [
    {
        "name": "TEST 1: MARATHI (मराठी) TEXT QUERY",
        "question": "सोयाबीनची पेरणी कधी करावी?",
        "language": "mr",
        "expected_code": "mr"
    },
    {
        "name": "TEST 2: HINDI (हिन्दी) TEXT QUERY",
        "question": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "language": "hi",
        "expected_code": "hi"
    },
    {
        "name": "TEST 3: ENGLISH TEXT QUERY",
        "question": "When should soybean be sown?",
        "language": "en",
        "expected_code": "en"
    }
]

for tc in test_cases:
    print("\n" + "#" * 60)
    print(f"▶ {tc['name']}")
    print("#" * 60)

    payload = {
        "question": tc["question"],
        "language": tc["language"]
    }

    resp = client.post("/ask", json=payload)
    assert resp.status_code == 200, f"Error: {resp.status_code} {resp.text}"
    res = resp.json()

    print("\n--- CLIENT RESPONSE VERIFICATION ---")
    print("HTTP Status:", resp.status_code)
    print("Language:", res.get("language"))
    print("Answer:", res.get("answer")[:100] + "...")
    print("Audio URL:", res.get("audio_url"))
    print("Audio MIME:", res.get("audio_mime_type"))
    
    b64 = res.get("audio_base64")
    print("Audio base64 present:", bool(b64))
    if b64:
        raw_bytes = base64.b64decode(b64)
        print("Decoded audio size:", round(len(raw_bytes) / 1024, 2), "KB")
        assert len(raw_bytes) > 5000, "Audio bytes too small!"
        print("✓ Audio payload is valid, non-empty, and ready for Streamlit playback!")
