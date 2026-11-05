import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import time
import uuid
import base64
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import settings
from backend.rag import retrieve_kcc_evidence, load_kcc_vectorstore
from backend.language import (
    detect_language,
    get_language_display_name,
    get_no_evidence_message,
    get_unintelligible_message,
    translate_to_target_language,
    is_text_in_target_language,
    is_meaningful_transcript
)
from backend.llm import generate_grounded_answer
from backend.voice import speech_to_text, text_to_speech
from backend.database import init_db, save_conversation, get_conversation_history, check_db_health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kisanvani_backend")

app = FastAPI(
    title=settings.APP_NAME,
    description="Voice-First Multilingual Agricultural Advisory Assistant with Canonical Selected Language Routing",
    version="2.5.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount audio files directory
os.makedirs(settings.AUDIO_INPUT_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_OUTPUT_DIR, exist_ok=True)
audio_root_dir = os.path.dirname(settings.AUDIO_INPUT_DIR)
app.mount("/audio", StaticFiles(directory=audio_root_dir), name="audio")

@app.on_event("startup")
async def startup_event():
    print("""
╔════════════════════════════════════════════════════════════╗
║                 🌾 KISANVANI BACKEND                     ║
╚════════════════════════════════════════════════════════════╝

✓ FastAPI
✓ Speech-to-text
✓ KCC knowledge base
✓ ICAR/KVK knowledge base
✓ Vector database
✓ SQLite database
✓ LLM
✓ Text-to-speech

Supported languages:
✓ English
✓ Hindi
✓ Marathi

Server:
http://localhost:8000
""")
    # Initialize SQLite database
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization notice: {e}")

    # Pre-warm vectorstore and embedding model so runtime requests are instant
    try:
        load_kcc_vectorstore()
    except Exception as e:
        logger.warning(f"Vectorstore warmup notice: {e}")

class AskRequest(BaseModel):
    question: str = Field(..., description="Farmer question in English, Hindi, or Marathi")
    language: Optional[str] = Field(None, description="Selected conversation language: 'en', 'hi', or 'mr'")

def parse_page_num(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

class SourceItem(BaseModel):
    source: str
    record_id: Optional[str] = None
    crop: Optional[str] = None
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    filename: Optional[str] = None
    file_name: Optional[str] = None
    page_number: Optional[int] = None
    language: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    similarity_distance: Optional[float] = None
    similarity_score: Optional[float] = None

class AskResponse(BaseModel):
    answer: str
    language: str
    spoken_language: Optional[str] = None
    selected_language: Optional[str] = None
    normalized_query: Optional[str] = None
    confidence: str
    is_grounded: bool
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_mime_type: Optional[str] = "audio/mpeg"
    audio_success: bool = True
    tts_error: Optional[str] = None
    source: str = "Agricultural Advisory Knowledge Base"
    sources: List[SourceItem]
    retrieved_records: List[Dict[str, Any]]
    latency_ms: float

class VoiceResponse(BaseModel):
    success: bool
    audio_success: bool = True
    transcript: str
    spoken_language: str
    selected_language: str
    detected_language: str
    normalized_query: str
    answer: str
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_mime_type: Optional[str] = "audio/mpeg"
    tts_error: Optional[str] = None
    source: str = "Agricultural Advisory Knowledge Base"
    confidence: str
    is_grounded: bool
    sources: List[SourceItem]
    retrieved_records: List[Dict[str, Any]]
    latency_ms: float

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
    language: str = Field("en", description="Language code: 'en', 'hi', or 'mr'")

class TTSResponse(BaseModel):
    success: bool
    language: str
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float

@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/status", tags=["System"])
async def system_status():
    """Returns system status, dataset records count, and vectorstore status."""
    vectorstore_loaded = False
    record_count = 0

    try:
        vs = load_kcc_vectorstore()
        vectorstore_loaded = vs is not None
        if vs and hasattr(vs, "index"):
            record_count = vs.index.ntotal
    except Exception:
        pass

    db_health = check_db_health()

    return {
        "app_name": settings.APP_NAME,
        "backend": "running",
        "vectorstore_ready": vectorstore_loaded,
        "record_count": record_count,
        "sqlite_ready": db_health.get("connected", False),
        "sqlite_connected": db_health.get("connected", False),
        "sqlite_database": "data/kisanvani.db",
        "supported_languages": ["mr", "hi", "en"],
        "embedding_model": settings.EMBEDDING_MODEL_NAME
    }

@app.post("/tts", response_model=TTSResponse, tags=["Audio"])
async def synthesize_speech_endpoint(req: TTSRequest):
    """Standalone Text-to-Speech endpoint for English, Hindi, and Marathi."""
    t0 = time.time()
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    lang = req.language if req.language in ["en", "hi", "mr"] else "mr"
    try:
        audio_url, audio_b64, file_path = text_to_speech(text, language_code=lang)
        latency = round((time.time() - t0) * 1000, 2)
        return TTSResponse(
            success=True,
            language=lang,
            audio_url=audio_url,
            audio_base64=audio_b64,
            file_path=file_path,
            latency_ms=latency
        )
    except Exception as e:
        latency = round((time.time() - t0) * 1000, 2)
        logger.error(f"Standalone TTS endpoint failed: {e}")
        return TTSResponse(
            success=False,
            language=lang,
            error=str(e),
            latency_ms=latency
        )

@app.get("/test-tts", tags=["Audio"])
async def test_all_tts():
    """Convenience endpoint to test all 3 supported languages in one call."""
    results = {}
    samples = {
        "en": "Hello farmer, KisanVani agricultural speech synthesis is working.",
        "hi": "नमस्कार किसान भाई, किसानवाणी हिंदी ध्वनि प्रणाली सक्रिय है।",
        "mr": "नमस्कार शेतकरी बंधूंनो, किसानवाणी मराठी ध्वनी प्रणाली सक्रिय आहे."
    }

    for lang, sample in samples.items():
        t0 = time.time()
        try:
            url, b64, path = text_to_speech(sample, language_code=lang)
            results[lang] = {
                "success": True,
                "audio_url": url,
                "audio_base64_len": len(b64) if b64 else 0,
                "latency_ms": round((time.time() - t0) * 1000, 2)
            }
        except Exception as err:
            results[lang] = {
                "success": False,
                "error": str(err),
                "latency_ms": round((time.time() - t0) * 1000, 2)
            }
    return results

@app.post("/voice", response_model=VoiceResponse, tags=["Advisory"])
async def process_voice_query(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Primary Farmer Voice Endpoint with Locked Selected Language Routing.
    Selected language directly controls Whisper STT language, RAG query, LLM response, and TTS.
    """
    t0 = time.time()
    req_id = f"KV-{uuid.uuid4().hex[:6].upper()}"
    selected_lang = language if language in ["en", "hi", "mr"] else "mr"
    selected_name = get_language_display_name(selected_lang)

    failing_stage = "Voice Input"
    try:
        audio_bytes = await audio_file.read()
        if not audio_bytes or len(audio_bytes) < 100:
            raise HTTPException(status_code=400, detail="Invalid or empty audio payload.")

        filename = audio_file.filename or "farmer_query.wav"
        orig_ext = filename.split(".")[-1].lower()
        if orig_ext not in ["webm", "wav", "mp3", "m4a", "ogg"]:
            orig_ext = "wav"
        fmt_display = orig_ext.upper()
        file_size_kb = round(len(audio_bytes) / 1024, 2)

        # Transcribe with forced Whisper language matching selected language
        failing_stage = "Speech-to-Text"
        transcript, spoken_lang, conf, raw_detected_lang, raw_prob, duration_sec, sample_rate = speech_to_text(
            audio_bytes=audio_bytes,
            language=selected_lang,
            original_ext=orig_ext,
            selected_language=selected_lang
        )

        print("\n" + "=" * 60)
        print("🌾 KISANVANI VOICE PIPELINE")
        print("=" * 60 + "\n")

        # [1] VOICE RECEIVED
        print("[1] 🎤 VOICE RECEIVED\n")
        print("Selected language:")
        print(f"{selected_name}\n")
        print("Audio:")
        print(f"{duration_sec:.2f} seconds\n")
        print("-" * 60 + "\n")

        # [2] SPEECH-TO-TEXT
        print("[2] 🔊 SPEECH-TO-TEXT\n")
        print("Forced Whisper language:")
        print(f"{selected_lang} ({selected_name})\n")
        print("Transcript:")
        print(f"\"{transcript}\"\n")
        print("-" * 60 + "\n")

        # Handle very short recordings (< 1.0 sec)
        if duration_sec < 0.8:
            print("⚠ Voice recording too short (< 1.0 sec).\n")
            short_msg = {
                "mr": "आवाज रेकॉर्डिंग खूप लहान आहे. कृपया पुन्हा बोला.",
                "hi": "आवाज रिकॉर्डिंग बहुत छोटी है। कृपया दोबारा बोलें।",
                "en": "Voice recording is too short. Please speak again."
            }.get(selected_lang, "Voice recording is too short. Please speak again.")

            audio_url, audio_b64, _ = text_to_speech(short_msg, language_code=selected_lang)
            return VoiceResponse(
                success=True,
                audio_success=True,
                transcript=transcript or "...",
                spoken_language=selected_lang,
                selected_language=selected_lang,
                detected_language=selected_lang,
                normalized_query=transcript or "...",
                answer=short_msg,
                audio_url=audio_url,
                audio_base64=audio_b64,
                source="Agricultural Advisory Knowledge Base",
                confidence="Low",
                is_grounded=False,
                sources=[],
                retrieved_records=[],
                latency_ms=round((time.time() - t0) * 1000, 2)
            )

        # Quality check for unintelligible audio
        if not is_meaningful_transcript(transcript):
            print("⚠ Low-quality / unintelligible speech detected.\n")
            answer = get_unintelligible_message(selected_lang)
            audio_url, audio_b64, _ = text_to_speech(answer, language_code=selected_lang)

            return VoiceResponse(
                success=True,
                audio_success=True,
                transcript=transcript,
                spoken_language=selected_lang,
                selected_language=selected_lang,
                detected_language=selected_lang,
                normalized_query=transcript,
                answer=answer,
                audio_url=audio_url,
                audio_base64=audio_b64,
                source="Agricultural Advisory Knowledge Base",
                confidence="Low",
                is_grounded=False,
                sources=[],
                retrieved_records=[],
                latency_ms=round((time.time() - t0) * 1000, 2)
            )

        # [3] LANGUAGE PROCESSING (Same language, no translation)
        failing_stage = "Language Processing"
        normalized_query = transcript
        print("[3] 🌐 LANGUAGE\n")
        print("Selected language:")
        print(f"{selected_name}\n")
        print("Speech language:")
        print(f"{selected_name}\n")
        print("Translation:")
        print("NOT REQUIRED\n")
        print("Normalized query:")
        print(f"\"{normalized_query}\"\n")
        print("-" * 60 + "\n")

        # [4] RAG RETRIEVAL
        failing_stage = "RAG Retrieval"
        print("[4] 🔎 RAG\n")
        print("Query:")
        print(f"\"{normalized_query}\"\n")
        print("Searching:\n")
        print("✓ Kisan Call Centre")
        print("✓ ICAR/KVK")
        print("✓ Agricultural PDFs\n")

        retrieved_records, confidence, is_grounded, context_str = retrieve_kcc_evidence(
            query=normalized_query,
            top_k=settings.TOP_K,
            language_code=selected_lang
        )

        print(f"Retrieved:\n{len(retrieved_records)} evidence records\n")
        print("-" * 60 + "\n")

        # [5] EVIDENCE
        top_rec = retrieved_records[0] if (is_grounded and retrieved_records) else {}
        top_src = top_rec.get("source", "Agricultural Advisory Knowledge Base")
        top_fn = top_rec.get("filename") or top_rec.get("file_name") or "knowledge_base"
        top_pg = str(top_rec.get("page_number")) if top_rec.get("page_number") else "N/A"
        top_sc = top_rec.get("similarity_score") if top_rec.get("similarity_score") is not None else top_rec.get("similarity_distance")
        top_sc_str = f"{top_sc:.2f}" if isinstance(top_sc, (int, float)) else "0.80"

        print("[5] 📚 EVIDENCE\n")
        print("Source:")
        print(f"{top_src}\n")
        print("File:")
        print(f"{top_fn}\n")
        print("Page:")
        print(f"{top_pg}\n")
        print("Relevance:")
        print(f"{top_sc_str}\n")
        print("-" * 60 + "\n")

        # [6] LLM ANSWER GENERATION
        failing_stage = "Answer Generation"
        print("[6] 🤖 LLM\n")
        print("Answer language:")
        print(f"{selected_name}\n")

        if is_grounded and retrieved_records:
            answer = generate_grounded_answer(
                question=normalized_query,
                retrieved_records=retrieved_records,
                context_str=context_str,
                language_code=selected_lang,
                confidence=confidence,
                is_grounded=is_grounded
            )

            # Enforce 100% selected language
            if not is_text_in_target_language(answer, selected_lang):
                answer = translate_to_target_language(answer, selected_lang)

            print("Grounded answer:")
            print(f"\"{answer}\"\n")
        else:
            answer = get_no_evidence_message(selected_lang)
            print("Grounded answer:")
            print(f"\"{answer}\"\n")

        print("-" * 60 + "\n")

        # [6] TEXT-TO-SPEECH
        failing_stage = "Text-to-Speech"
        print("=" * 60)
        print("[6] 🔊 TEXT-TO-SPEECH")
        print("=" * 60 + "\n")
        print("Input language:")
        print(f"{selected_name}\n")
        print("TTS language:")
        print(f"{selected_name}\n")
        print("TTS code:")
        print(f"{selected_lang}\n")
        print("Generating audio...\n")

        audio_url = None
        audio_b64 = None
        tts_error = None
        tts_success = True
        audio_size_kb = 0.0
        try:
            audio_url, audio_b64, output_path = text_to_speech(answer, language_code=selected_lang)
            if audio_b64:
                audio_size_kb = round(len(base64.b64decode(audio_b64)) / 1024, 2)
            print("✓ Audio generated")
            print(f"Audio size: {audio_size_kb:.2f} KB")
            print("MIME: audio/mpeg")
            print("Base64: YES\n")
        except Exception as tts_err:
            tts_error = str(tts_err)
            tts_success = False
            print(f"✗ Audio generation failed ({tts_error})\n")

        # [7] RESPONSE
        print("=" * 60)
        print("[7] 📤 RESPONSE")
        print("=" * 60 + "\n")
        print("Text response:\n✓\n")
        print(f"Audio response:\n{'✓' if tts_success else '✗'}\n")
        print(f"Audio bytes:\n{audio_size_kb:.2f} KB\n")

        print("=" * 60)
        print("🌾 KISANVANI PIPELINE COMPLETE")
        print("=" * 60 + "\n")
        print("Voice response:")
        print("✓ Generated")
        print("✓ Returned to frontend\n")
        print("=" * 60 + "\n")

        # Format Sources
        sources = [
            SourceItem(
                source=r.get("source", "Agricultural Advisory"),
                record_id=r.get("record_id"),
                crop=r.get("crop"),
                category=r.get("category"),
                question=r.get("question"),
                answer=r.get("answer"),
                filename=r.get("filename") or r.get("file_name"),
                file_name=r.get("filename") or r.get("file_name"),
                page_number=parse_page_num(r.get("page_number")),
                language=r.get("language"),
                location=r.get("location"),
                date=r.get("date"),
                similarity_distance=r.get("similarity_distance"),
                similarity_score=r.get("similarity_score")
            )
            for r in retrieved_records
        ]

        # Save to SQLite Database (Additive, non-blocking)
        try:
            save_conversation(
                request_id=req_id,
                input_type="voice",
                question=transcript,
                transcript=transcript,
                spoken_language=selected_lang,
                selected_language=selected_lang,
                normalized_query=normalized_query,
                answer=answer,
                source=top_src,
                source_file=top_fn if top_fn != "knowledge_base" else None,
                page_number=parse_page_num(top_pg) if top_pg != "N/A" else None,
                retrieval_score=float(top_sc) if isinstance(top_sc, (int, float)) else None,
                processing_time=round(time.time() - t0, 3)
            )
        except Exception as db_err:
            logger.warning(f"Non-blocking SQLite save notice in /voice: {db_err}")

        latency_ms = round((time.time() - t0) * 1000, 2)

        return VoiceResponse(
            success=True,
            audio_success=tts_success,
            transcript=transcript,
            spoken_language=selected_lang,
            selected_language=selected_lang,
            detected_language=selected_lang,
            normalized_query=normalized_query,
            answer=answer,
            audio_url=audio_url,
            audio_base64=audio_b64,
            audio_mime_type="audio/mpeg",
            tts_error=tts_error,
            source="Agricultural Advisory Knowledge Base",
            confidence=confidence,
            is_grounded=is_grounded,
            sources=sources,
            retrieved_records=retrieved_records,
            latency_ms=latency_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("[ERROR] ❌ PIPELINE FAILED")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print(f"Stage: {failing_stage}")
        print(f"Request ID: {req_id}\n")
        print(f"Error:\n{str(e)}\n")
        logger.exception(f"Unhandled error in /voice (Request {req_id}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse, tags=["Advisory"])
async def ask_question(req: AskRequest):
    """
    Direct Text & Example Question Endpoint with Canonical Selected Language Routing.
    Generates grounded text answer and synthesized voice advisory audio.
    """
    t0 = time.time()
    req_id = f"KV-{uuid.uuid4().hex[:4].upper()}"
    query_text = req.question.strip()
    if not query_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")

    spoken_lang = detect_language(query_text)
    selected_lang = req.language if req.language in ["en", "hi", "mr"] else "mr"
    selected_lang_name = get_language_display_name(selected_lang)

    print("\n" + "=" * 60)
    print("[TEXT QUERY]")
    print("=" * 60 + "\n")
    print("Question:")
    print(f'"{query_text}"\n')
    print("Selected language:")
    print(f"{selected_lang_name}\n")

    # 1. Query Normalization (if query language doesn't match selected language)
    if spoken_lang == selected_lang:
        normalized_query = query_text
    else:
        normalized_query = translate_to_target_language(query_text, selected_lang)

    # 2. RAG Retrieval with normalized_query
    retrieved_records, confidence, is_grounded, context_str = retrieve_kcc_evidence(
        query=normalized_query,
        top_k=settings.TOP_K,
        language_code=selected_lang
    )

    print("[RAG]")
    print(f"Retrieved: {len(retrieved_records)} records\n")

    # 3. Grounded Answer Generation
    answer = generate_grounded_answer(
        question=normalized_query,
        retrieved_records=retrieved_records,
        context_str=context_str,
        language_code=selected_lang,
        confidence=confidence,
        is_grounded=is_grounded
    )

    # Validate output language
    if is_grounded and not is_text_in_target_language(answer, selected_lang):
        answer = translate_to_target_language(answer, selected_lang)

    print("[GEMINI]")
    print("Answer generated ✓\n")

    # 4. Text-to-Speech Synthesis
    print("[TTS]")
    print(f"Language: {selected_lang_name}")
    print(f"Code: {selected_lang}\n")
    print("Generating audio...\n")

    audio_url = None
    audio_b64 = None
    audio_size_kb = 0.0
    tts_success = True
    tts_error = None

    try:
        audio_url, audio_b64, output_path = text_to_speech(answer, language_code=selected_lang)
        if audio_b64:
            audio_size_kb = round(len(base64.b64decode(audio_b64)) / 1024, 2)
        print("Audio generated:")
        print("✓\n")
        print("Audio size:")
        print(f"{audio_size_kb:.2f} KB\n")
        print("MIME:")
        print("audio/mpeg\n")
    except Exception as tts_err:
        tts_error = str(tts_err)
        tts_success = False
        print(f"Audio generation failed: {tts_error}\n")

    # 5. Response Completion
    print("[RESPONSE]")
    print("Text:")
    print("✓\n")
    print("Audio:")
    print(f"{'✓' if tts_success else '✗'}\n")
    print("=" * 60 + "\n")

    total_duration = round(time.time() - t0, 2)
    latency_ms = round(total_duration * 1000, 2)

    # Format Sources
    sources = [
        SourceItem(
            source=r.get("source", "Agricultural Advisory"),
            record_id=r.get("record_id"),
            crop=r.get("crop"),
            category=r.get("category"),
            question=r.get("question"),
            answer=r.get("answer"),
            filename=r.get("filename") or r.get("file_name"),
            file_name=r.get("filename") or r.get("file_name"),
            page_number=parse_page_num(r.get("page_number")),
            language=r.get("language"),
            location=r.get("location"),
            date=r.get("date"),
            similarity_distance=r.get("similarity_distance"),
            similarity_score=r.get("similarity_score")
        )
        for r in retrieved_records
    ]

    # Save to SQLite Database (Additive, non-blocking)
    top_rec = retrieved_records[0] if (is_grounded and retrieved_records) else {}
    top_src = top_rec.get("source", "Agricultural Advisory Knowledge Base")
    top_fn = top_rec.get("filename") or top_rec.get("file_name")
    top_pg = parse_page_num(top_rec.get("page_number"))
    top_sc = top_rec.get("similarity_score") if top_rec.get("similarity_score") is not None else top_rec.get("similarity_distance")

    try:
        save_conversation(
            request_id=req_id,
            input_type="text",
            question=query_text,
            transcript=None,
            spoken_language=spoken_lang,
            selected_language=selected_lang,
            normalized_query=normalized_query,
            answer=answer,
            source=top_src,
            source_file=top_fn if top_fn != "knowledge_base" else None,
            page_number=top_pg,
            retrieval_score=float(top_sc) if isinstance(top_sc, (int, float)) else None,
            processing_time=round(time.time() - t0, 3)
        )
    except Exception as db_err:
        logger.warning(f"Non-blocking SQLite save notice in /ask: {db_err}")

    return AskResponse(
        answer=answer,
        language=selected_lang,
        spoken_language=spoken_lang,
        selected_language=selected_lang,
        normalized_query=normalized_query,
        confidence=confidence,
        is_grounded=is_grounded,
        audio_url=audio_url,
        audio_base64=audio_b64,
        audio_mime_type="audio/mpeg",
        audio_success=tts_success,
        tts_error=tts_error,
        source="Agricultural Advisory Knowledge Base",
        sources=sources,
        retrieved_records=retrieved_records,
        latency_ms=latency_ms
    )
