import os
import sys
import io
import time
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.rag import load_kcc_vectorstore, get_embeddings_model

# Synthetic 16kHz mono audio generator
def create_mock_wav_bytes(duration_sec: float = 3.5, sample_rate: int = 16000) -> bytes:
    import wave
    import struct
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

# Pre-warm vectorstore
get_embeddings_model()
load_kcc_vectorstore()

test_cases = [
    {
        "name": "TEST 1: MARATHI (मराठी)",
        "selected_lang": "mr",
        "spoken_text": "सोयाबीनची पेरणी कधी करावी?",
        "expected_whisper_lang": "mr"
    },
    {
        "name": "TEST 2: HINDI (हिन्दी)",
        "selected_lang": "hi",
        "spoken_text": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "expected_whisper_lang": "hi"
    },
    {
        "name": "TEST 3: ENGLISH",
        "selected_lang": "en",
        "spoken_text": "When should soybean be sown?",
        "expected_whisper_lang": "en"
    }
]

mock_audio = create_mock_wav_bytes(3.5, 16000)

for tc in test_cases:
    print("\n" + "#" * 60)
    print(f"▶ {tc['name']}")
    print("#" * 60)

    with patch("backend.main.speech_to_text") as mock_stt:
        # Mock STT output matching locked whisper language transcription
        mock_stt.return_value = (
            tc["spoken_text"],
            tc["selected_lang"],
            0.98,
            tc["selected_lang"],
            0.98,
            3.50,
            16000
        )

        files = {
            "audio_file": ("farmer_query.wav", mock_audio, "audio/wav")
        }
        data = {
            "language": tc["selected_lang"]
        }

        resp = client.post("/voice", files=files, data=data)
        print(f"HTTP Status: {resp.status_code}")
        res = resp.json()
        assert resp.status_code == 200
        print(f"Transcript: {res.get('transcript')}")
        print(f"Spoken Language: {res.get('spoken_language')}")
        print(f"Selected Language: {res.get('selected_language')}")
        print(f"Normalized Query: {res.get('normalized_query')}")
        print(f"Answer: {res.get('answer')[:100]}...")
