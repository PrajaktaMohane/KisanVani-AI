import logging
from typing import Optional, Dict, Any
from app.db.mongo import db_manager
from app.models.farmer import FarmerCreate, FarmerProfile

logger = logging.getLogger(__name__)

class FarmerRepository:
    collection_name = "farmers"

    @classmethod
    def get_collection(cls):
        db = db_manager.get_database()
        if db is not None:
            return db[cls.collection_name]
        return None

    @classmethod
    async def create_or_update_farmer(cls, phone_number: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            logger.warning("MongoDB not available; skipping farmer profile save.")
            return data

        await coll.update_one(
            {"phone_number": phone_number},
            {"$set": data},
            upsert=True
        )
        return await coll.find_one({"phone_number": phone_number})

    @classmethod
    async def get_farmer_by_phone(cls, phone_number: str) -> Optional[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return None
        return await coll.find_one({"phone_number": phone_number})
