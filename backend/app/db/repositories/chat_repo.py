import logging
import time
from typing import Optional, Dict, Any, List
from app.db.mongo import db_manager

logger = logging.getLogger(__name__)

# In-memory session store fallback if MongoDB is not running
_in_memory_logs: List[Dict[str, Any]] = []

class ChatRepository:
    collection_name = "conversations"

    @classmethod
    def get_collection(cls):
        db = db_manager.get_database()
        if db is not None:
            return db[cls.collection_name]
        return None

    @classmethod
    async def log_interaction(cls, log_data: Dict[str, Any]):
        if "created_at" not in log_data:
            log_data["created_at"] = time.time()

        coll = cls.get_collection()
        if coll is not None:
            try:
                await coll.insert_one(log_data)
                return
            except Exception as e:
                logger.warning(f"Failed to log interaction to MongoDB: {e}")

        # In-memory append
        _in_memory_logs.append(log_data)

    @classmethod
    async def get_history_by_session(cls, session_id: str) -> List[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is not None:
            try:
                cursor = coll.find({"session_id": session_id}).sort("created_at", 1)
                results = await cursor.to_list(length=50)
                # Convert ObjectId to string
                for r in results:
                    if "_id" in r:
                        r["_id"] = str(r["_id"])
                return results
            except Exception as e:
                logger.warning(f"Failed to read from MongoDB: {e}")

        # In-memory filter
        return [
            {**log, "_id": str(idx)}
            for idx, log in enumerate(_in_memory_logs)
            if log.get("session_id") == session_id
        ]

    @classmethod
    async def get_all_recent(cls, limit: int = 50) -> List[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is not None:
            try:
                cursor = coll.find().sort("created_at", -1)
                results = await cursor.to_list(length=limit)
                for r in results:
                    if "_id" in r:
                        r["_id"] = str(r["_id"])
                return results
            except Exception as e:
                logger.warning(f"Failed to read recent from MongoDB: {e}")

        # Return in-memory logs reversed
        return [
            {**log, "_id": str(idx)}
            for idx, log in enumerate(reversed(_in_memory_logs[-limit:]))
        ]

class FeedbackRepository:
    collection_name = "feedback"

    @classmethod
    def get_collection(cls):
        db = db_manager.get_database()
        if db is not None:
            return db[cls.collection_name]
        return None

    @classmethod
    async def record_feedback(cls, feedback_data: Dict[str, Any]):
        coll = cls.get_collection()
        if coll is not None:
            try:
                await coll.insert_one(feedback_data)
                return
            except Exception:
                pass
        logger.info(f"Feedback recorded (in-memory): {feedback_data}")
