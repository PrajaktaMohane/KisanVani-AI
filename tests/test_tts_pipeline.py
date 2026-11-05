import os
import io
import sys
import pytest
from gtts import gTTS
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.voice import text_to_speech

client = TestClient(app)

# 1. Test Standalone text_to_speech function across all 3 languages
def test_tts_function_english():
    text = "Sowing time for kharif soybean is June to July."
    url, b64, path = text_to_speech(text, language_code="en")
    assert url is not None
    assert b64 is not None
    assert len(b64) > 100
    assert os.path.exists(path)

def test_tts_function_hindi():
    text = "गेहूं में पहली सिंचाई सीआरआई अवस्था पर करें।"
    url, b64, path = text_to_speech(text, language_code="hi")
    assert url is not None
    assert b64 is not None
    assert len(b64) > 100
    assert os.path.exists(path)

def test_tts_function_marathi():
    text = "कापसावरील बोंडअळीच्या नियंत्रणासाठी फेरोमोन ट्रॅप लावावेत."
    url, b64, path = text_to_speech(text, language_code="mr")
    assert url is not None
    assert b64 is not None
    assert len(b64) > 100
    assert os.path.exists(path)

# 2. Test Standalone /tts Endpoint
def test_tts_endpoint_english():
    resp = client.post("/tts", json={"text": "Hello farmer, testing voice output.", "language": "en"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["language"] == "en"
    assert data["audio_base64"] is not None

def test_tts_endpoint_marathi():
    resp = client.post("/tts", json={"text": "नमस्कार शेतकरी बंधूंनो", "language": "mr"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["language"] == "mr"
    assert data["audio_base64"] is not None

def test_test_all_tts_endpoint():
    resp = client.get("/test-tts")
    assert resp.status_code == 200
    data = resp.json()
    assert "en" in data and data["en"]["success"] is True
    assert "hi" in data and data["hi"]["success"] is True
    assert "mr" in data and data["mr"]["success"] is True

# 3. Test Graceful Fallback in /voice when TTS fails (No HTTP 500)
def test_voice_endpoint_graceful_on_tts_failure():
    tts_test = gTTS(text="cotton pest remedy", lang="en", slow=False)
    audio_fp = io.BytesIO()
    tts_test.write_to_fp(audio_fp)
    audio_fp.seek(0)

    files = {"audio_file": ("query.mp3", audio_fp, "audio/mp3")}
    data = {"language": "en"}

    # Mock text_to_speech to simulate a network connection failure
    with patch("backend.main.text_to_speech", side_effect=RuntimeError("Failed to connect. Probable cause: Unknown")):
        resp = client.post("/voice", files=files, data=data)
        
        # Crucial check: Must NOT return 500
        assert resp.status_code == 200, f"Expected 200 on TTS failure, got {resp.status_code}"
        res_data = resp.json()
        assert res_data["success"] is True
        assert res_data["audio_success"] is False
        assert "answer" in res_data
        assert res_data["audio_base64"] is None
        assert "Failed to connect" in str(res_data.get("tts_error"))

# 4. Test Complete /voice Endpoint Pipeline When TTS Works
def test_voice_endpoint_full_pipeline_success():
    tts_test = gTTS(text="soybean sowing time", lang="en", slow=False)
    audio_fp = io.BytesIO()
    tts_test.write_to_fp(audio_fp)
    audio_fp.seek(0)

    files = {"audio_file": ("query.mp3", audio_fp, "audio/mp3")}
    data = {"language": "en"}

    resp = client.post("/voice", files=files, data=data)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["audio_success"] is True
    assert "answer" in res_data
    assert res_data["audio_base64"] is not None
    assert len(res_data["audio_base64"]) > 100
    assert "sources" in res_data
    assert "detected_language" in res_data
