import sys
import os
import io
import sqlite3
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings
from backend.rag import load_kcc_vectorstore, get_embeddings_model
from backend.database import init_db, get_conversation_history, check_db_health

def make_wav_bytes(duration_sec=3.5, sample_rate=16000):
    import wave, struct
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        num_frames = int(duration_sec * sample_rate)
        data = struct.pack("<" + "h" * num_frames, *([100] * num_frames))
        wav.writeframes(data)
    return buf.getvalue()

client = TestClient(app)
get_embeddings_model()
load_kcc_vectorstore()
init_db()

print("=" * 60)
print("TEST 1 — TEXT QUERY (मराठी)")
print("=" * 60)

text_payload = {
    "question": "सोयाबीनची पेरणी कधी करावी?",
    "language": "mr"
}

resp_text = client.post("/ask", json=text_payload)
assert resp_text.status_code == 200, f"Error: {resp_text.status_code} {resp_text.text}"
res_t = resp_text.json()
print("✓ Text Answer:", res_t.get("answer")[:80] + "...")
print("✓ Audio base64 present:", bool(res_t.get("audio_base64")))
print("✓ Audio MIME:", res_t.get("audio_mime_type"))

print("\n" + "=" * 60)
print("TEST 2 — VOICE QUERY (मराठी)")
print("=" * 60)

mock_audio = make_wav_bytes(3.5, 16000)

with patch("backend.main.speech_to_text") as mock_stt:
    mock_stt.return_value = (
        "सोयाबीनची पेरणी कधी करावी?",
        "mr",
        0.98,
        "mr",
        0.98,
        3.50,
        16000
    )

    files = {
        "audio_file": ("farmer_query.wav", mock_audio, "audio/wav")
    }
    data = {
        "language": "mr"
    }

    resp_voice = client.post("/voice", files=files, data=data)
    assert resp_voice.status_code == 200, f"Error: {resp_voice.status_code} {resp_voice.text}"
    res_v = resp_voice.json()
    print("✓ Transcript:", res_v.get("transcript"))
    print("✓ Voice Answer:", res_v.get("answer")[:80] + "...")
    print("✓ Audio base64 present:", bool(res_v.get("audio_base64")))

print("\n" + "=" * 60)
print("SQLITE DATABASE VERIFICATION")
print("=" * 60)
print(f"Database file path: {settings.SQLITE_DB_PATH}")
print(f"File exists: {os.path.exists(settings.SQLITE_DB_PATH)}")
print(f"File size: {os.path.getsize(settings.SQLITE_DB_PATH)} bytes")

health = check_db_health()
print(f"Database health: {health}")

conn = sqlite3.connect(settings.SQLITE_DB_PATH)
cursor = conn.cursor()

print("\n--- SCHEMA ---")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='conversation_history';")
schema = cursor.fetchone()[0]
print(schema)

print("\n--- RECORDS IN CONVERSATION_HISTORY (LAST 5) ---")
cursor.execute("""
    SELECT id, request_id, input_type, selected_language, question, source, created_at
    FROM conversation_history
    ORDER BY id DESC
    LIMIT 5;
""")
rows = cursor.fetchall()
for r in rows:
    print(f"ID: {r[0]} | ReqID: {r[1]} | Type: {r[2]} | Lang: {r[3]} | Query: \"{r[4]}\" | Source: {r[5]} | Time: {r[6]}")

conn.close()
