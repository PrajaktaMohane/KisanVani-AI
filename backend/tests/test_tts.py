import pytest
from app.services.tts_service import TTSService

def test_tts_synthesis_multilingual():
    """Verify that speech audio is generated for Marathi, Hindi, and English."""
    cases = [
        ("कापसावरील गुलाबी बोंड अळीसाठी ५ फेरोमन ट्रॅप लावावेत.", "mr"),
        ("गेहूं में पहली सिंचाई २१ दिन बाद करें।", "hi"),
        ("Always wear protective gloves and mask while spraying.", "en")
    ]

    for text, lang in cases:
        audio_bytes, audio_b64 = TTSService.synthesize_speech(text=text, language_code=lang)
        assert audio_bytes is not None
        assert len(audio_bytes) > 100
        assert audio_b64 is not None
        assert len(audio_b64) > 100
