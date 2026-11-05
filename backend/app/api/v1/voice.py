import time
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.models.voice import VoiceQueryResponse
from app.services.audio_utils import convert_audio_to_wav, cleanup_temp_file
from app.services.stt_service import STTService
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.tts_service import TTSService
from app.db.repositories.chat_repo import ChatRepository

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=VoiceQueryResponse)
@router.post("/query", response_model=VoiceQueryResponse)
async def process_voice_query(
    audio_file: UploadFile = File(..., description="Farmer voice recording (webm, wav, mp3, ogg)"),
    session_id: Optional[str] = Form(None),
    farmer_id: Optional[str] = Form(None),
    state: Optional[str] = Form("Maharashtra"),
    district: Optional[str] = Form(None),
    crop_name: Optional[str] = Form(None),
    soil_type: Optional[str] = Form("Black soil"),
    land_size_acres: Optional[float] = Form(2.5),
    preferred_language: Optional[str] = Form(None)
):
    """
    Main Voice Pipeline:
    Farmer Voice (Browser MediaRecorder)
      ↓
    Whisper STT & Language Detection (mr/hi/en)
      ↓
    FAISS Metadata RAG Retrieval
      ↓
    Gemini 1.5 Flash (Grounded Krishi Mitra Persona & Dosage Safety)
      ↓
    TTS Audio Synthesis
      ↓
    Return Voice Response + Transcript + Sources
    """
    start_total = time.time()
    latency_breakdown = {}
    sid = session_id or f"session_{uuid.uuid4().hex[:10]}"

    temp_wav_path = None
    try:
        # Step 1: Read and convert audio
        t0 = time.time()
        file_bytes = await audio_file.read()
        file_ext = audio_file.filename.split(".")[-1] if "." in audio_file.filename else "webm"
        temp_wav_path = convert_audio_to_wav(file_bytes, original_extension=file_ext)

        # Step 2: Speech to Text (Whisper)
        transcript, detected_lang, confidence = STTService.transcribe(
            temp_wav_path,
            language=preferred_language
        )
        latency_breakdown["stt_ms"] = round((time.time() - t0) * 1000, 2)
        logger.info(f"Transcript: '{transcript}' | Detected Lang: {detected_lang}")

        # Step 3: RAG Retrieval (FAISS)
        t1 = time.time()
        context_str, sources, is_grounded = RAGService.retrieve_grounded_context(
            query=transcript,
            crop=crop_name
        )
        latency_breakdown["rag_ms"] = round((time.time() - t1) * 1000, 2)

        # Step 4: Gemini LLM Agricultural Advisory
        t2 = time.time()
        answer_text = await LLMService.generate_agricultural_advisory(
            farmer_query=transcript,
            retrieved_context=context_str,
            detected_language=detected_lang,
            is_grounded=is_grounded,
            farmer_state=state,
            farmer_district=district,
            crop_name=crop_name,
            soil_type=soil_type,
            land_size_acres=land_size_acres
        )
        latency_breakdown["llm_ms"] = round((time.time() - t2) * 1000, 2)

        # Step 5: Text to Speech Synthesis
        t3 = time.time()
        audio_bytes, audio_b64 = TTSService.synthesize_speech(
            text=answer_text,
            language_code=detected_lang
        )
        latency_breakdown["tts_ms"] = round((time.time() - t3) * 1000, 2)
        latency_breakdown["total_ms"] = round((time.time() - start_total) * 1000, 2)

        # Step 6: Log conversation in database
        try:
            await ChatRepository.log_interaction({
                "session_id": sid,
                "farmer_id": farmer_id,
                "query_transcript": transcript,
                "detected_language": detected_lang,
                "is_grounded": is_grounded,
                "response_text": answer_text,
                "sources": [s.model_dump() for s in sources],
                "latency_breakdown": latency_breakdown,
                "created_at": time.time()
            })
        except Exception as db_err:
            logger.warning(f"Could not persist conversation: {db_err}")

        return VoiceQueryResponse(
            success=True,
            transcript=transcript,
            detected_language=detected_lang,
            answer_text=answer_text,
            audio_base64=audio_b64,
            sources=sources,
            latency_breakdown_ms=latency_breakdown
        )

    finally:
        if temp_wav_path:
            cleanup_temp_file(temp_wav_path)

@router.post("/transcribe")
async def transcribe_only(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None)
):
    """
    Dedicated endpoint for testing Speech-to-Text and language detection.
    """
    temp_wav_path = None
    try:
        file_bytes = await audio_file.read()
        file_ext = audio_file.filename.split(".")[-1] if "." in audio_file.filename else "webm"
        temp_wav_path = convert_audio_to_wav(file_bytes, original_extension=file_ext)

        transcript, detected_lang, confidence = STTService.transcribe(temp_wav_path, language=language)
        return {
            "transcript": transcript,
            "detected_language": detected_lang,
            "confidence": confidence
        }
    finally:
        if temp_wav_path:
            cleanup_temp_file(temp_wav_path)
