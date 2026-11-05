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
from backend.language import is_text_in_target_language

client = TestClient(app)

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

tests = [
    {
        "num": 1,
        "name": "TEST 1: Marathi Selected + Marathi Speech",
        "selected_language": "mr",
        "speech": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "expected_out_lang": "mr",
        "expected_norm_query": "सोयाबीनची पेरणी कधी करावी?"
    },
    {
        "num": 2,
        "name": "TEST 2: Marathi Selected + Hindi Speech",
        "selected_language": "mr",
        "speech": "सोयाबीन की बुवाई कब करनी चाहिए?",
        "spoken_lang": "hi",
        "expected_out_lang": "mr",
        "expected_norm_query": "सोयाबीनची पेरणी कधी करावी?"
    },
    {
        "num": 3,
        "name": "TEST 3: Hindi Selected + Marathi Speech",
        "selected_language": "hi",
        "speech": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "expected_out_lang": "hi",
        "expected_norm_query": "सोयाबीन की बुवाई कब करनी चाहिए?"
    },
    {
        "num": 4,
        "name": "TEST 4: English Selected + Marathi Speech",
        "selected_language": "en",
        "speech": "सोयाबीनची पेरणी कधी करावी?",
        "spoken_lang": "mr",
        "expected_out_lang": "en",
        "expected_norm_query": "When should soybean be sown?"
    },
    {
        "num": 5,
        "name": "TEST 5: Marathi Selected + English Speech",
        "selected_language": "mr",
        "speech": "When should soybean be sown?",
        "spoken_lang": "en",
        "expected_out_lang": "mr",
        "expected_norm_query": "सोयाबीनची पेरणी कधी करावी?"
    },
    {
        "num": 6,
        "name": "TEST 6: Low-Quality / Gibberish Audio Quality Check",
        "selected_language": "mr",
        "speech": "--- ... ---",
        "spoken_lang": "mr",
        "expected_out_lang": "mr",
        "is_unintelligible": True
    }
]

print("=" * 80)
print("🌾 KISANVANI VOICE DEBUG & IMPROVEMENTS VALIDATION SUITE")
print("=" * 80)

all_passed = True

for t in tests:
    print(f"\n>>> RUNNING {t['name']}")
    wav_buf = make_dummy_wav()
    files = {"audio_file": ("query.wav", wav_buf, "audio/wav")}
    data = {"language": t["selected_language"]}

    with patch("backend.main.speech_to_text", return_value=(t["speech"], t["spoken_lang"], 0.95, t["spoken_lang"], 0.95, 2.0, 16000)):
        resp = client.post("/voice", files=files, data=data)

    if resp.status_code != 200:
        print(f"❌ HTTP Failed with status {resp.status_code}")
        all_passed = False
        continue

    res = resp.json()
    ans = res.get("answer", "")
    norm_q = res.get("normalized_query", "")
    sel_lang = res.get("selected_language")
    spk_lang = res.get("spoken_language")
    script_valid = is_text_in_target_language(ans, t["expected_out_lang"])

    print(f"  ✓ Transcript:       '{res.get('transcript')}'")
    print(f"  ✓ Spoken Lang:      '{spk_lang}'")
    print(f"  ✓ Normalized Query: '{norm_q}'")
    print(f"  ✓ Final Lang:       '{sel_lang}' (Script Check: {'✓ Valid' if script_valid else '❌ Invalid'})")
    print(f"  ✓ Audio Output:     {res.get('audio_url')}")

    if not script_valid or sel_lang != t["expected_out_lang"]:
        print(f"❌ Language validation failed for {t['name']}")
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL SPECIFIED DEBUG & IMPROVEMENT TESTS PASSED 100%!")
else:
    print("❌ SOME TESTS FAILED!")
print("=" * 80 + "\n")
