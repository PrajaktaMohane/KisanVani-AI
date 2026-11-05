import os
import sqlite3
import datetime
import logging
from typing import Optional, List, Dict, Any

from backend.config import settings

logger = logging.getLogger(__name__)

LANGUAGE_DISPLAY_MAP = {
    "mr": "Marathi",
    "hi": "Hindi",
    "en": "English"
}

def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.SQLITE_DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> bool:
    """
    Initializes SQLite database and creates the conversation_history table if it doesn't exist.
    Safe and non-blocking: never raises unhandled exceptions.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE,
                input_type TEXT,
                question TEXT,
                transcript TEXT,
                spoken_language TEXT,
                selected_language TEXT,
                normalized_query TEXT,
                answer TEXT,
                source TEXT,
                source_file TEXT,
                page_number INTEGER,
                retrieval_score REAL,
                processing_time REAL,
                created_at TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_req_id ON conversation_history(request_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_created ON conversation_history(created_at);")
        conn.commit()
        conn.close()
        logger.info(f"SQLite database initialized at: {settings.SQLITE_DB_PATH}")
        return True
    except Exception as e:
        logger.warning(f"⚠ SQLite initialization notice: {e}")
        return False

def save_conversation(
    request_id: str,
    input_type: str,
    question: Optional[str] = None,
    transcript: Optional[str] = None,
    spoken_language: Optional[str] = None,
    selected_language: Optional[str] = None,
    normalized_query: Optional[str] = None,
    answer: Optional[str] = None,
    source: Optional[str] = None,
    source_file: Optional[str] = None,
    page_number: Optional[int] = None,
    retrieval_score: Optional[float] = None,
    processing_time: Optional[float] = None,
    created_at: Optional[str] = None
) -> bool:
    """
    Persists a completed advisory conversation record into SQLite.
    Never raises an exception — logs success or graceful failure notice.
    """
    selected_lang_name = LANGUAGE_DISPLAY_MAP.get(selected_language, selected_language or "Marathi")
    query_display = question or transcript or "..."
    source_display = source or "Agricultural Advisory Knowledge Base"

    if created_at is None:
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        print("\n" + "=" * 60)
        print("[DATABASE]")
        print("=" * 60 + "\n")
        print("SQLite:\ndata/kisanvani.db\n")
        print("Saving conversation...\n")
        print(f"Request ID:\n{request_id}\n")
        print(f"Input type:\n{input_type}\n")
        print(f"Selected language:\n{selected_lang_name}\n")
        print(f"Question:\n\"{query_display}\"\n")
        print(f"Source:\n{source_display}\n")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO conversation_history (
                request_id,
                input_type,
                question,
                transcript,
                spoken_language,
                selected_language,
                normalized_query,
                answer,
                source,
                source_file,
                page_number,
                retrieval_score,
                processing_time,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            request_id,
            input_type,
            question,
            transcript,
            spoken_language,
            selected_language,
            normalized_query,
            answer,
            source_display,
            source_file,
            page_number,
            retrieval_score,
            processing_time,
            created_at
        ))
        conn.commit()
        conn.close()

        print("✓ Conversation saved\n")
        print("=" * 60 + "\n")
        return True

    except Exception as e:
        print(f"⚠ SQLite save failed\n\nReason:\n{str(e)}\n")
        print("=" * 60 + "\n")
        logger.warning(f"Failed to persist conversation history: {e}")
        return False

def get_conversation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves the recent conversation history records ordered by id DESC."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, request_id, input_type, question, transcript,
                   spoken_language, selected_language, normalized_query,
                   answer, source, source_file, page_number,
                   retrieval_score, processing_time, created_at
            FROM conversation_history
            ORDER BY id DESC
            LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Failed to query conversation history: {e}")
        return []

def check_db_health() -> Dict[str, Any]:
    """Health status check for SQLite persistence layer."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversation_history;")
        count = cursor.fetchone()[0]
        conn.close()
        return {
            "connected": True,
            "database": "data/kisanvani.db",
            "total_conversations": count
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "database": "data/kisanvani.db",
            "total_conversations": 0
        }

#sqlite3 data/kisanvani.db
#SELECT * FROM conversation_history ORDER BY id DESC LIMIT 5;
