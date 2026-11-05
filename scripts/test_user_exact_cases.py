import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import io
import sys
import wave
import struct
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

client = TestClient(app)

def make_sample_wav():
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        data = struct.pack("<" + "h" * 16000, *([100] * 16000))
        wav.writeframes(data)
    buf.seek(0)
    return buf

test_cases = [
    {
        "name": "TEST 1: Selected = Marathi | Spoken = Marathi ('सोयाबीनची पेरणी कधी करावी?')",
        "selected_lang": "mr",
        "spoken_text": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "conf": 0.96
    },
    {
        "name": "TEST 2: Selected = Marathi | Spoken = Hindi ('सोयाबीन की बुवाई कब करनी चाहिए?')",
        "selected_lang": "mr",
        "spoken_text": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "spoken_lang": "hi",
        "conf": 0.94
    },
    {
        "name": "TEST 3: Selected = Marathi | Spoken = English ('When should soybean be sown?')",
        "selected_lang": "mr",
        "spoken_text": "When should soybean be sown?",
        "spoken_lang": "en",
        "conf": 0.98
    },
    {
        "name": "TEST 4: Selected = Hindi | Spoken = Marathi ('सोयाबीनची पेरणी कधी करावी?')",
        "selected_lang": "hi",
        "spoken_text": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "conf": 0.95
    },
    {
        "name": "TEST 5: Selected = English | Spoken = Marathi ('सोयाबीनची पेरणी कधी करावी?')",
        "selected_lang": "en",
        "spoken_text": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "conf": 0.95
    }
]

for tc in test_cases:
    print("\n" + "#" * 70)
    print(f"▶ {tc['name']}")
    print("#" * 70)

    wav_buf = make_sample_wav()
    files = {"audio_file": ("farmer_query.wav", wav_buf, "audio/wav")}
    data = {"language": tc["selected_lang"]}

    with patch("backend.main.speech_to_text", return_value=(
        tc["spoken_text"],
        tc["spoken_lang"],
        tc["conf"],
        tc["spoken_lang"],
        tc["conf"],
        4.80,
        16000
    )):
        resp = client.post("/voice", files=files, data=data)

    print(f"HTTP Response: {resp.status_code}")
