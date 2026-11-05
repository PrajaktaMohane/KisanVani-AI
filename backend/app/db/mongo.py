import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    @classmethod
    async def connect_to_database(cls):
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
            cls.client = AsyncIOMotorClient(settings.MONGO_URI)
            cls.db = cls.client[settings.MONGO_DB_NAME]
            # Verify connection
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}. Running with limited persistence.")

    @classmethod
    async def close_database_connection(cls):
        if cls.client:
            logger.info("Closing MongoDB connection...")
            cls.client.close()
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        return cls.db

db_manager = MongoDBManager()
