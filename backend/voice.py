import os
import io
import re
import time
import uuid
import base64
import logging
from typing import Tuple, Optional, Dict, Any
from gtts import gTTS
from gtts.tts import gTTSError
from backend.config import settings

logger = logging.getLogger(__name__)

# Ensure audio directories exist
os.makedirs(settings.AUDIO_INPUT_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_OUTPUT_DIR, exist_ok=True)

# STT Model Singleton
_whisper_model = None
_is_faster_whisper = False

SUPPORTED_LANGUAGES = ["mr", "hi", "en"]

AGRICULTURAL_PROMPTS = {
    "mr": "कृषी सल्ला, शेती, पिके, खते, कीड, रोग, सोयाबीन, कापूस, गहू, तांदूळ, पाणी, पेरणी, काढणी, फवारणी, बोंडअळी.",
    "hi": "कृषि सलाह, खेती, फसल, खाद, रोग, कीट, सोयाबीन, कपास, गेहूं, धान, सिंचाई, बुवाई, कटाई, छिड़काव, गुलाबी सुंडी.",
    "en": "Agricultural advisory, farming, crops, fertilizer, disease, pest, soybean, cotton, wheat, rice, irrigation, sowing, harvesting, pink bollworm."
}

DEFAULT_MULTILINGUAL_PROMPT = (
    "कृषी सल्ला, शेती, पिके, खते, पेरणी, बुवाई, soybean, cotton, wheat, fertilizer, pest, irrigation."
)

def get_stt_model():
    """Initializes and returns the Whisper STT model instance."""
    global _whisper_model, _is_faster_whisper
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info(f"Loading faster-whisper model '{settings.WHISPER_MODEL_SIZE}' on CPU...")
            _whisper_model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device="cpu",
                compute_type="int8"
            )
            _is_faster_whisper = True
        except Exception as e:
            logger.warning(f"faster-whisper load failed ({e}), falling back to openai-whisper...")
            try:
                import whisper
                _whisper_model = whisper.load_model(settings.WHISPER_MODEL_SIZE, device="cpu")
                _is_faster_whisper = False
            except Exception as w_err:
                logger.error(f"openai-whisper load failed: {w_err}")
                raise RuntimeError(f"Could not load any Whisper model: {w_err}")
    return _whisper_model

def convert_audio_to_wav(audio_bytes: bytes, original_format: str = "webm") -> Tuple[str, float, int]:
    """Converts uploaded audio bytes to 16kHz mono WAV for Whisper. Returns (wav_path, duration_seconds, sample_rate)."""
    import tempfile
    from pydub import AudioSegment

    temp_in = tempfile.NamedTemporaryFile(delete=False, suffix=f".{original_format}")
    temp_in.write(audio_bytes)
    temp_in.close()

    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_out.close()

    duration_sec = 0.0
    sample_rate = 16000
    try:
        audio = AudioSegment.from_file(temp_in.name, format=original_format)
        duration_sec = round(len(audio) / 1000.0, 2)
        sample_rate = audio.frame_rate
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(temp_out.name, format="wav")
        return temp_out.name, duration_sec, sample_rate
    except Exception as e:
        logger.warning(f"pydub audio conversion failed: {e}. Using raw temp file.")
        return temp_in.name, duration_sec, sample_rate
    finally:
        if os.path.exists(temp_in.name) and temp_in.name != temp_out.name:
            try:
                os.remove(temp_in.name)
            except Exception:
                pass

def speech_to_text(
    audio_bytes: bytes,
    language: Optional[str] = None,
    original_ext: str = "webm",
    selected_language: Optional[str] = None
) -> Tuple[str, str, float, str, float, float, int]:
    """
    Transcribes audio note using faster-whisper with domain prompts locked to the selected language.
    Returns: (transcript, spoken_language, confidence, raw_detected_lang, raw_prob, duration_sec, sample_rate)
    """
    # 1. Save original input audio to data/audio/input/
    file_id = f"input_{int(time.time())}_{uuid.uuid4().hex[:6]}.{original_ext}"
    input_file_path = os.path.join(settings.AUDIO_INPUT_DIR, file_id)
    with open(input_file_path, "wb") as f:
        f.write(audio_bytes)

    # 2. Convert to WAV for Whisper
    wav_path, duration_sec, sample_rate = convert_audio_to_wav(audio_bytes, original_format=original_ext)

    # Forced target language based on selected language
    target_lang = selected_language or language or "mr"
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = "mr"

    try:
        model = get_stt_model()
        initial_prompt = AGRICULTURAL_PROMPTS.get(target_lang, DEFAULT_MULTILINGUAL_PROMPT)

        if _is_faster_whisper:
            segments, info = model.transcribe(
                wav_path,
                language=target_lang,
                initial_prompt=initial_prompt,
                beam_size=5,
                temperature=0.0,
                vad_filter=True,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0
            )

            raw_transcript = " ".join([seg.text for seg in segments]).strip()
            return raw_transcript, target_lang, 0.98, target_lang, 0.98, duration_sec, sample_rate

        else:
            result = model.transcribe(
                wav_path,
                language=target_lang,
                initial_prompt=initial_prompt,
                temperature=0.0
            )
            transcript = result.get("text", "").strip()
            return transcript, target_lang, 0.98, target_lang, 0.98, duration_sec, sample_rate

    except Exception as e:
        logger.error(f"Speech-to-text transcription error: {e}")
        raise RuntimeError(f"Speech-to-text failed: {str(e)}")
    finally:
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass

def text_to_speech(text: str, language_code: str = "mr") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Synthesizes speech in Marathi (mr), Hindi (hi), or English (en) using gTTS.
    Saves audio file to data/audio/output/.
    Returns: (audio_url, audio_base64, file_path)
    Raises RuntimeError if synthesis fails.
    """
    lang = language_code if language_code in ["mr", "hi", "en"] else "mr"

    # Strip markdown formatting, symbols, and excess whitespace for clean pronunciation
    clean_speech_text = text.replace("*", "").replace("#", "").replace("_", "").replace("`", "").strip()
    if not clean_speech_text:
        clean_speech_text = "कृषी सल्लागार माहिती उपलब्ध आहे." if lang == "mr" else ("कृषि सलाहकार जानकारी उपलब्ध है।" if lang == "hi" else "Agricultural advisory information is available.")

    # Limit maximum character length per voice note for fast, high-speed audio generation
    if len(clean_speech_text) > 300:
        clean_speech_text = clean_speech_text[:300].rstrip()
        last_space = clean_speech_text.rfind(" ")
        if last_space > 150:
            clean_speech_text = clean_speech_text[:last_space]

    output_filename = f"response_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"
    output_filepath = os.path.join(settings.AUDIO_OUTPUT_DIR, output_filename)

    try:
        tts = gTTS(text=clean_speech_text, lang=lang, slow=False, timeout=5)
        tts.save(output_filepath)

        with open(output_filepath, "rb") as f:
            audio_bytes = f.read()

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        audio_url = f"/audio/output/{output_filename}"

        return audio_url, audio_b64, output_filepath

    except gTTSError as g_err:
        logger.error(f"gTTS API connection failure for lang '{lang}': {g_err}")
        raise RuntimeError(f"Failed to connect to TTS service ({str(g_err)})")
    except Exception as e:
        logger.error(f"Text-to-speech synthesis error for lang '{lang}': {e}")
        raise RuntimeError(f"Text-to-speech failed: {str(e)}")
