import time
import uuid
import logging
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.models.voice import VoiceQueryResponse
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.tts_service import TTSService
from app.db.repositories.chat_repo import ChatRepository

router = APIRouter()
logger = logging.getLogger(__name__)

class TextQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    farmer_id: Optional[str] = None
    state: Optional[str] = "Maharashtra"
    district: Optional[str] = None
    crop_name: Optional[str] = None
    soil_type: Optional[str] = "Black soil"
    land_size_acres: Optional[float] = 2.5
    language: Optional[str] = "hi"
    include_audio: bool = True

class TTSRequest(BaseModel):
    text: str
    language: str = "hi"

@router.post("", response_model=VoiceQueryResponse)
@router.post("/query", response_model=VoiceQueryResponse)
async def process_text_query(req: TextQueryRequest):
    """
    Main Text Query Endpoint:
    Processes farmer text questions through RAG & Gemini with optional TTS voice generation.
    """
    start_total = time.time()
    latency_breakdown = {}
    sid = req.session_id or f"session_{uuid.uuid4().hex[:10]}"

    # Step 1: RAG Retrieval
    t1 = time.time()
    context_str, sources, is_grounded = RAGService.retrieve_grounded_context(
        query=req.query,
        crop=req.crop_name
    )
    latency_breakdown["rag_ms"] = round((time.time() - t1) * 1000, 2)

    # Step 2: Gemini Generation with Guardrails
    t2 = time.time()
    answer_text = await LLMService.generate_agricultural_advisory(
        farmer_query=req.query,
        retrieved_context=context_str,
        detected_language=req.language or "hi",
        is_grounded=is_grounded,
        farmer_state=req.state or "Maharashtra",
        farmer_district=req.district,
        crop_name=req.crop_name,
        soil_type=req.soil_type,
        land_size_acres=req.land_size_acres
    )
    latency_breakdown["llm_ms"] = round((time.time() - t2) * 1000, 2)

    # Step 3: Optional TTS Synthesis
    audio_b64 = None
    if req.include_audio:
        t3 = time.time()
        _, audio_b64 = TTSService.synthesize_speech(
            text=answer_text,
            language_code=req.language or "hi"
        )
        latency_breakdown["tts_ms"] = round((time.time() - t3) * 1000, 2)

    latency_breakdown["total_ms"] = round((time.time() - start_total) * 1000, 2)

    # Step 4: Persist in Database
    try:
        await ChatRepository.log_interaction({
            "session_id": sid,
            "farmer_id": req.farmer_id,
            "query_transcript": req.query,
            "detected_language": req.language or "hi",
            "is_grounded": is_grounded,
            "response_text": answer_text,
            "sources": [s.model_dump() for s in sources],
            "latency_breakdown": latency_breakdown,
            "created_at": time.time()
        })
    except Exception as e:
        logger.warning(f"Could not log interaction: {e}")

    return VoiceQueryResponse(
        success=True,
        transcript=req.query,
        detected_language=req.language or "hi",
        answer_text=answer_text,
        audio_base64=audio_b64,
        sources=sources,
        latency_breakdown_ms=latency_breakdown
    )

@router.post("/tts")
async def generate_speech_only(req: TTSRequest):
    """
    Direct Text-to-Speech synthesis test endpoint.
    """
    audio_bytes, audio_b64 = TTSService.synthesize_speech(
        text=req.text,
        language_code=req.language
    )
    return {
        "text": req.text,
        "language": req.language,
        "audio_base64": audio_b64,
        "audio_bytes_length": len(audio_bytes)
    }

@router.get("/conversations")
async def get_conversations(limit: int = 30):
    """
    Retrieves recent conversations and query history for the chat UI sidebar.
    """
    history = await ChatRepository.get_all_recent(limit=limit)
    return {"conversations": history}

@router.get("/conversations/{session_id}")
async def get_conversation_thread(session_id: str):
    """
    Retrieves the full message thread for a specific conversation session.
    """
    messages = await ChatRepository.get_history_by_session(session_id)
    return {"session_id": session_id, "messages": messages}
