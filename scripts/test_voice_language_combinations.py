import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import io
import sys
import time
import wave
import struct
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.language import is_text_in_target_language

client = TestClient(app)

print("=" * 85)
print("🌾 KISANVANI 9-COMBINATION VOICE & CANONICAL LANGUAGE PIPELINE TEST")
print("=" * 85)

combinations = [
    # 1. Marathi Selected
    {
        "id": "1",
        "selected_language": "mr",
        "speech_text": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "expected_out_lang": "mr",
        "desc": "Marathi Selected + Marathi Speech"
    },
    {
        "id": "2",
        "selected_language": "mr",
        "speech_text": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "spoken_lang": "hi",
        "expected_out_lang": "mr",
        "desc": "Marathi Selected + Hindi Speech"
    },
    {
        "id": "3",
        "selected_language": "mr",
        "speech_text": "When should soybean be sown?",
        "spoken_lang": "en",
        "expected_out_lang": "mr",
        "desc": "Marathi Selected + English Speech"
    },

    # 2. Hindi Selected
    {
        "id": "4",
        "selected_language": "hi",
        "speech_text": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "spoken_lang": "hi",
        "expected_out_lang": "hi",
        "desc": "Hindi Selected + Hindi Speech"
    },
    {
        "id": "5",
        "selected_language": "hi",
        "speech_text": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "expected_out_lang": "hi",
        "desc": "Hindi Selected + Marathi Speech"
    },
    {
        "id": "6",
        "selected_language": "hi",
        "speech_text": "When should soybean be sown?",
        "spoken_lang": "en",
        "expected_out_lang": "hi",
        "desc": "Hindi Selected + English Speech"
    },

    # 3. English Selected
    {
        "id": "7",
        "selected_language": "en",
        "speech_text": "When should soybean be sown?",
        "spoken_lang": "en",
        "expected_out_lang": "en",
        "desc": "English Selected + English Speech"
    },
    {
        "id": "8",
        "selected_language": "en",
        "speech_text": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "expected_out_lang": "en",
        "desc": "English Selected + Marathi Speech"
    },
    {
        "id": "9",
        "selected_language": "en",
        "speech_text": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "spoken_lang": "hi",
        "expected_out_lang": "en",
        "desc": "English Selected + Hindi Speech"
    }
]

def make_dummy_wav():
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        data = struct.pack("<" + "h" * 16000, *([100] * 16000))
        wav.writeframes(data)
    buf.seek(0)
    return buf

all_passed = True

for tc in combinations:
    print(f"\n[{tc['id']}/9] Testing: {tc['desc']}")
    print(f"  • Selected Canonical Language: {tc['selected_language'].upper()}")
    print(f"  • Farmer Spoken Speech:         '{tc['speech_text']}' ({tc['spoken_lang'].upper()})")

    # Call /voice endpoint with mocked Whisper STT to test the exact audio payload flow
    wav_buf = make_dummy_wav()
    files = {"audio_file": ("farmer_input.wav", wav_buf, "audio/wav")}
    data = {"language": tc["selected_language"]}

    with patch("backend.main.speech_to_text", return_value=(tc["speech_text"], tc["spoken_lang"], 0.98, tc["spoken_lang"], 0.98, 2.5, 16000)):
        resp = client.post("/voice", files=files, data=data)

    if resp.status_code != 200:
        print(f"  ❌ FAILED: HTTP {resp.status_code}")
        all_passed = False
        continue

    res_data = resp.json()
    transcript = res_data.get("transcript")
    detected_spoken = res_data.get("spoken_language")
    selected_lang = res_data.get("selected_language")
    norm_query = res_data.get("normalized_query")
    answer = res_data.get("answer", "")
    audio_url = res_data.get("audio_url")
    audio_b64 = res_data.get("audio_base64")
    
    is_script_correct = is_text_in_target_language(answer, tc["expected_out_lang"])
    
    print(f"  ✓ Transcript Captured:          '{transcript}'")
    print(f"  ✓ Spoken Lang Detected:         '{detected_spoken}'")
    print(f"  ✓ Normalized Query:             '{norm_query}'")
    print(f"  ✓ Final Response Language:      '{selected_lang}' (Script Valid: {is_script_correct})")
    print(f"  ✓ TTS Audio Generated:          {bool(audio_b64)} (URL: {audio_url})")
    print(f"  ✓ Answer Sample:\n    {answer[:180]}...")

    if not is_script_correct or selected_lang != tc["expected_out_lang"]:
        print("  ❌ Language check failed!")
        all_passed = False

print("\n" + "=" * 85)
if all_passed:
    print("✅ ALL 9 VOICE LANGUAGE COMBINATIONS PASSED (100% CANONICAL LANGUAGE MATCH)!")
else:
    print("❌ SOME COMBINATIONS FAILED!")
print("=" * 85 + "\n")
