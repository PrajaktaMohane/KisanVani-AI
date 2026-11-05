import io
import base64
import logging
from typing import Tuple
from gtts import gTTS
from app.core.config import settings
from app.core.exceptions import TextToSpeechException

logger = logging.getLogger(__name__)

# Mapping of ISO language codes to Google TTS voice codes
LANGUAGE_VOICE_MAP = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "pa": "pa-IN",
    "en": "en-IN"
}

class TTSService:

    @classmethod
    def synthesize_speech(cls, text: str, language_code: str = "hi") -> Tuple[bytes, str]:
        """
        Converts text to speech audio bytes (MP3 format) and returns (audio_bytes, base64_encoded_audio).
        """
        lang = language_code if language_code in LANGUAGE_VOICE_MAP else "hi"

        try:
            # First attempt Google Cloud TTS if credentials are provided
            if settings.TTS_ENGINE == "google-cloud" and settings.GOOGLE_APPLICATION_CREDENTIALS:
                from google.cloud import texttospeech
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=text)
                voice_name = f"{LANGUAGE_VOICE_MAP.get(lang, 'hi-IN')}-Standard-A"
                voice = texttospeech.VoiceSelectionParams(
                    language_code=LANGUAGE_VOICE_MAP.get(lang, "hi-IN"),
                    name=voice_name
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )
                audio_bytes = response.audio_content
            else:
                # Default high-compatibility gTTS (Google Translate TTS)
                tts = gTTS(text=text, lang=lang, slow=False)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_bytes = fp.read()

            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return audio_bytes, audio_b64

        except Exception as e:
            logger.error(f"TTS synthesis failed for lang {language_code}: {e}")
            # Fallback to English gTTS if regional TTS throws an error
            try:
                tts = gTTS(text=text, lang="en", slow=False)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_bytes = fp.read()
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                return audio_bytes, audio_b64
            except Exception as inner_e:
                raise TextToSpeechException(detail=f"Speech synthesis failed: {str(inner_e)}")
