import os
import io
import sys
import pytest
from unittest.mock import patch
from gtts import gTTS
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.config import settings
from backend.data_loader import clean_text, is_unusable_record, extract_metadata, discover_all_pdfs, extract_and_chunk_pdf
from backend.language import detect_language, get_no_evidence_message
from backend.rag import retrieve_kcc_evidence

client = TestClient(app)

# 1. Dataset Loading & PDF Chunking Tests
def test_data_cleaning_unusable_records():
    assert is_unusable_record("", "") is True
    assert is_unusable_record("short", "ans") is True
    assert is_unusable_record("what to spray on mustard aphid", "explained in detail") is True
    assert is_unusable_record("what to spray on mustard aphid", "call disconnected") is True
    assert is_unusable_record(
        "asking about the control measure for aphid infestation in mustard crops",
        "suggested him to spray rogor@2ml/lit.at evening time."
    ) is False

def test_pdf_discovery_and_chunking():
    search_dirs = [os.path.join(settings.BASE_DIR, "data")]
    pdfs = discover_all_pdfs(search_dirs)
    assert len(pdfs) >= 1, "Should discover at least 1 agricultural PDF in data/"
    
    # Test chunking on first discovered PDF
    first_pdf = pdfs[0]
    chunks = extract_and_chunk_pdf(first_pdf, chunk_size=750, chunk_overlap=120)
    assert len(chunks) > 0, "Should extract non-empty chunks from PDF"
    assert "page_number" in chunks[0]
    assert "file_name" in chunks[0]
    assert "source" in chunks[0]

def test_metadata_extraction():
    meta = extract_metadata("control of aphid in mustard crops. Spray rogor at 2ml per liter")
    assert meta["crop"] == "Mustard"
    assert meta["category"] == "Pest & Disease Management"

    meta2 = extract_metadata("coconut flower drop problem. Apply planofix and urea")
    assert meta2["crop"] == "Coconut"
    assert meta2["category"] == "Flower & Fruit Drop"

# 2. Language Detection Tests
def test_language_detection_multilingual():
    assert detect_language("What pesticide should I spray for pink bollworm in cotton?") == "en"
    assert detect_language("सरसों में माहू कीट नियंत्रण के लिए क्या करें?") == "hi"
    assert detect_language("कापसावरील गुलाबी बोंड अळीचे नियंत्रण कसे करावे?") == "mr"

# 3. Backend Health & Status Endpoints
def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_status_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "running"
    assert "record_count" in data

# 4. Multi-Source RAG Retrieval Tests (PDF & KCC)
def test_ask_icar_pdf_soybean():
    payload = {
        "question": "What is the recommended sowing time and fertilizer dose for soybean in kharif season?",
        "language": "en"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    assert "answer" in data
    assert len(data["sources"]) > 0
    # Check that sources contain ICAR or KCC
    sources_text = [s.get("source", "") for s in data["sources"]]
    assert any("ICAR" in s or "Kisan" in s or "Agricultural" in s for s in sources_text)

def test_ask_hindi_wheat():
    payload = {
        "question": "गेहूं की फसल में पहली सिंचाई कब करनी चाहिए?",
        "language": "hi"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "hi"
    assert "answer" in data

def test_ask_marathi_cotton_bollworm():
    payload = {
        "question": "कापसावरील गुलाबी बोंड अळीचे नियंत्रण कसे करावे?",
        "language": "mr"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "mr"
    assert "answer" in data

# 5. Irrelevant / Out of Domain Refusal (Zero-Hallucination Guardrail)
def test_irrelevant_question_no_hallucination():
    payload = {
        "question": "How to construct a quantum teleportation logic gate with topological qubits?",
        "language": "en"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_grounded"] is False or data["confidence"] == "Low" or "Verified information" in data["answer"] or "knowledge base" in data["answer"].lower()

# 6. /voice Endpoint Test (Full Voice In -> Unified RAG -> Voice Out)
def test_voice_endpoint_pipeline():
    import wave
    import struct
    
    # Generate 1 second offline WAV audio file
    audio_fp = io.BytesIO()
    with wave.open(audio_fp, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        # 16000 samples of quiet tone
        samples = [int(1000 * (i % 32 < 16)) for i in range(16000)]
        data = struct.pack("<" + "h" * 16000, *samples)
        wav_file.writeframes(data)
    audio_fp.seek(0)

    files = {
        "audio_file": ("test_farmer_voice.wav", audio_fp, "audio/wav")
    }
    data = {
        "language": "en"
    }

    # Mock STT transcription so test does not depend on microphone speech
    with patch("backend.main.speech_to_text", return_value=("soybean sowing time in kharif", "en", 0.95, "en", 0.95, 1.0, 16000)):
        response = client.post("/voice", files=files, data=data)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["success"] is True
        assert "transcript" in res_data
        assert "answer" in res_data
        assert "sources" in res_data
