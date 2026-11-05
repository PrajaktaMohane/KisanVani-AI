import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import sys
import logging
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.language import is_text_in_target_language

client = TestClient(app)

print("=" * 80)
print("🌐 KISANVANI LANGUAGE ENFORCEMENT & TRANSLATION VALIDATION")
print("=" * 80)

test_cases = [
    {
        "name": "Marathi Question with English ICAR Source (Soybean Sowing)",
        "question": "सोयाबीनची पेरणी कधी करावी?",
        "selected_language": "mr",
        "expected_lang": "mr"
    },
    {
        "name": "Hindi Question with English ICAR Source (Cotton Bollworm)",
        "question": "कपास में गुलाबी सुंडी होने पर क्या करें?",
        "selected_language": "hi",
        "expected_lang": "hi"
    },
    {
        "name": "English Question with English ICAR Source (Wheat Fertilizer)",
        "question": "Which fertilizer should be used for wheat?",
        "selected_language": "en",
        "expected_lang": "en"
    },
    {
        "name": "Marathi Language Selected with General Sowing Query",
        "question": "पिकाची पेरणी करण्यासाठी योग्य वेळ कोणती?",
        "selected_language": "mr",
        "expected_lang": "mr"
    },
    {
        "name": "Hindi Language Selected with Rice Irrigation Query",
        "question": "धान में पानी कैसे देना चाहिए?",
        "selected_language": "hi",
        "expected_lang": "hi"
    },
    {
        "name": "Irrelevant Query (Zero-Hallucination Fallback in Marathi)",
        "question": "शेअर बाजारात गुंतवणूक कशी करावी?",
        "selected_language": "mr",
        "expected_lang": "mr"
    },
    {
        "name": "Irrelevant Query (Zero-Hallucination Fallback in Hindi)",
        "question": "शेयर बाजार में निवेश कैसे करें?",
        "selected_language": "hi",
        "expected_lang": "hi"
    },
    {
        "name": "Irrelevant Query (Zero-Hallucination Fallback in English)",
        "question": "How to invest in cryptocurrency stock market?",
        "selected_language": "en",
        "expected_lang": "en"
    }
]

all_passed = True

for idx, tc in enumerate(test_cases, 1):
    print(f"\n--- TEST CASE {idx}: {tc['name']} ---")
    print(f"Question:          {tc['question']}")
    print(f"Selected Language: {tc['selected_language'].upper()}")

    resp = client.post("/ask", json={
        "question": tc["question"],
        "language": tc["selected_language"]
    })

    if resp.status_code != 200:
        print(f"❌ HTTP ERROR: Status {resp.status_code}")
        all_passed = False
        continue

    data = resp.json()
    answer = data.get("answer", "")
    resp_lang = data.get("language")
    is_valid_lang = is_text_in_target_language(answer, tc["expected_lang"])

    print(f"Response Language: {resp_lang}")
    print(f"Language Match:    {'✓ PASS' if resp_lang == tc['expected_lang'] and is_valid_lang else '❌ FAIL'}")
    print(f"Audio URL:         {data.get('audio_url')}")
    print(f"Top Source:        {data['sources'][0]['source'] if data.get('sources') else 'N/A'}")
    print(f"Final Answer Text:\n{answer}")

    if resp_lang != tc["expected_lang"] or not is_valid_lang:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL LANGUAGE ENFORCEMENT & TRANSLATION TESTS PASSED (100% MATCH)!")
else:
    print("❌ SOME LANGUAGE TESTS FAILED!")
print("=" * 80 + "\n")
