import logging
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import SpeechToTextException

logger = logging.getLogger(__name__)

class STTService:
    _model = None

    @classmethod
    def _get_whisper_model(cls):
        if cls._model is None:
            try:
                # Try faster-whisper first for high speed and low memory
                from faster_whisper import WhisperModel
                logger.info(f"Loading faster-whisper model: {settings.WHISPER_MODEL_SIZE} on {settings.WHISPER_DEVICE}")
                cls._model = WhisperModel(
                    settings.WHISPER_MODEL_SIZE,
                    device=settings.WHISPER_DEVICE,
                    compute_type="int8" if settings.WHISPER_DEVICE == "cpu" else "float16"
                )
                cls._is_faster_whisper = True
            except Exception as e:
                logger.warning(f"faster-whisper not available ({e}), falling back to openai-whisper...")
                import whisper
                cls._model = whisper.load_model(settings.WHISPER_MODEL_SIZE, device=settings.WHISPER_DEVICE)
                cls._is_faster_whisper = False
        return cls._model

    @classmethod
    def transcribe(cls, audio_file_path: str, language: str = None) -> Tuple[str, str, float]:
        """
        Transcribes the given audio file.
        Returns: (transcript_text, detected_language_code, confidence)
        """
        try:
            model = cls._get_whisper_model()

            if getattr(cls, "_is_faster_whisper", False):
                segments, info = model.transcribe(
                    audio_file_path,
                    language=language,
                    beam_size=5,
                    vad_filter=True
                )
                transcript = " ".join([segment.text for segment in segments]).strip()
                detected_language = info.language
                confidence = info.language_probability
                return transcript, detected_language, confidence
            else:
                result = model.transcribe(audio_file_path, language=language)
                transcript = result.get("text", "").strip()
                detected_language = result.get("language", "hi")
                return transcript, detected_language, 0.95

        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            raise SpeechToTextException(detail=f"Speech-to-text conversion failed: {str(e)}")
