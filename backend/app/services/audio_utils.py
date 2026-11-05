import os
import tempfile
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def convert_audio_to_wav(input_bytes: bytes, original_extension: str = "webm") -> str:
    """
    Converts incoming audio bytes (webm, ogg, mp4, etc.) to 16kHz mono WAV format
    optimized for Whisper speech-to-text.
    Returns path to temporary WAV file.
    """
    temp_in = tempfile.NamedTemporaryFile(suffix=f".{original_extension}", delete=False)
    temp_in.write(input_bytes)
    temp_in.flush()
    temp_in.close()

    temp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_out.close()

    try:
        audio = AudioSegment.from_file(temp_in.name)
        # Convert to 16kHz, mono
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(temp_out.name, format="wav")
        return temp_out.name
    except Exception as e:
        logger.error(f"Error converting audio to WAV: {e}")
        # Return original temp path if pydub conversion fails
        return temp_in.name
    finally:
        if os.path.exists(temp_in.name):
            try:
                os.remove(temp_in.name)
            except Exception:
                pass

def cleanup_temp_file(file_path: str):
    """Removes a temporary audio file if it exists."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file {file_path}: {e}")
