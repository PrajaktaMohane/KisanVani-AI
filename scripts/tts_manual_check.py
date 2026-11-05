import os
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.voice import text_to_speech

test_cases = [
    ("en", "Hello farmer, this is KisanVani agricultural assistant testing English speech synthesis."),
    ("hi", "नमस्ते किसान भाई, यह किसानवाणी कृषि सलाहकार हिंदी ध्वनि परीक्षण है।"),
    ("mr", "नमस्कार शेतकरी बंधूंनो, हे किसानवाणी कृषी सल्लागार मराठी ध्वनी चाचणी आहे.")
]

print("=" * 80)
print("🔊 STANDALONE TTS TEST (English, Hindi, Marathi)")
print("=" * 80)

for lang, text in test_cases:
    print(f"\nTesting Language: {lang.upper()}")
    print(f"Input Text: {text}")
    try:
        url, b64, path = text_to_speech(text, language_code=lang)
        print(f"  ✓ SUCCESS!")
        print(f"    Audio URL:  {url}")
        print(f"    File Path:  {path}")
        print(f"    File Size:  {os.path.getsize(path):,} bytes")
        print(f"    Base64 Len: {len(b64):,} chars")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        traceback.print_exc()

print("\n" + "=" * 80)
