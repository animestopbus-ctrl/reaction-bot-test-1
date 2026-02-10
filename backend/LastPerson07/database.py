from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel
from typing import Optional
from LastPerson07.config import settings
from LastPerson07.logger import logger


class Database:
    """Production-grade async MongoDB manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB and create indexes"""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
            )
            cls.db = cls.client[settings.DATABASE_NAME]
            
            await cls._create_indexes()
            
            await cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls):
        """Create all required indexes for optimal performance"""
        
        users_indexes = [
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("telegram_id", ASCENDING)], unique=True, sparse=True),
            IndexModel([("email", ASCENDING)], sparse=True),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("role", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
        await cls.db.users.create_indexes(users_indexes)
        
        reactions_indexes = [
            IndexModel([("chat_id", ASCENDING)]),
            IndexModel([("message_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("emoji", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("chat_id", ASCENDING), ("timestamp", DESCENDING)]),
        ]
        await cls.db.reactions.create_indexes(reactions_indexes)
        
        chats_indexes = [
            IndexModel([("chat_id", ASCENDING)], unique=True),
            IndexModel([("enabled", ASCENDING)]),
            IndexModel([("chat_type", ASCENDING)]),
            IndexModel([("added_at", DESCENDING)]),
        ]
        await cls.db.chats.create_indexes(chats_indexes)
        
        analytics_indexes = [
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("metric_type", ASCENDING)]),
            IndexModel([("date", DESCENDING)]),
            IndexModel([("hour", DESCENDING)]),
        ]
        await cls.db.analytics.create_indexes(analytics_indexes)
        
        settings_indexes = [
            IndexModel([("key", ASCENDING)], unique=True),
            IndexModel([("updated_at", DESCENDING)]),
        ]
        await cls.db.settings.create_indexes(settings_indexes)
        
        logger.info("Successfully created all database indexes")
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a collection from the database"""
        if cls.db is None:
            raise RuntimeError("Database not connected")
        return cls.db[name]


db = Database
