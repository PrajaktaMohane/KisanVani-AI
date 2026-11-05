import sys
import os
import io
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.rag import load_kcc_vectorstore, get_embeddings_model

# Generate test WAV audio
def make_wav_bytes(duration_sec=3.5, sample_rate=16000):
    import wave, struct
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        num_frames = int(duration_sec * sample_rate)
        data = struct.pack("<" + "h" * num_frames, *([100] * num_frames))
        wav.writeframes(data)
    return buf.getvalue()

client = TestClient(app)
get_embeddings_model()
load_kcc_vectorstore()

mock_audio = make_wav_bytes(3.5, 16000)

print("\n" + "=" * 60)
print("TESTING VOICE PIPELINE WITH REAL TTS AUDIO GENERATION")
print("=" * 60)

with patch("backend.main.speech_to_text") as mock_stt:
    mock_stt.return_value = (
        "सोयाबीनची पेरणी कधी करावी?",
        "mr",
        0.98,
        "mr",
        0.98,
        3.50,
        16000
    )

    files = {
        "audio_file": ("farmer_query.wav", mock_audio, "audio/wav")
    }
    data = {
        "language": "mr"
    }

    resp = client.post("/voice", files=files, data=data)
    assert resp.status_code == 200, f"Error: {resp.status_code} {resp.text}"
    res = resp.json()

    print("\n--- CLIENT RESPONSE VERIFICATION ---")
    print("HTTP Status:", resp.status_code)
    print("Transcript:", res.get("transcript"))
    print("Answer length:", len(res.get("answer", "")))
    print("Audio URL:", res.get("audio_url"))
    print("Audio MIME type:", res.get("audio_mime_type"))
    
    b64 = res.get("audio_base64")
    print("Audio base64 present:", bool(b64))
    if b64:
        print("Audio base64 length:", len(b64))
        raw_bytes = base64.b64decode(b64)
        print("Decoded audio bytes size:", round(len(raw_bytes) / 1024, 2), "KB")
        assert len(raw_bytes) > 5000, "Audio bytes too small!"
        print("✓ Audio data is valid and non-empty!")

