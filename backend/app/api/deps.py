from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongo import db_manager

async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Dependency provider for MongoDB database instance."""
    db = db_manager.get_database()
    yield db
