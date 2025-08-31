import os
from pymongo import MongoClient
from configs import settings

def get_mongodb():
    """
    Establish connection to MongoDB and return database instance.
    
    Returns:
        Database: MongoDB database instance
        
    Raises:
        ValueError: If MONGO_URL environment variable is not set
    """
    mongo_url = settings.MONGO_URL
    if not mongo_url:
        raise ValueError("MONGO_URL environment variable is required")
    
    client = MongoClient(mongo_url)
    db = client[settings.MONGO_DB]
    return db


if __name__ == "__main__":
    try:
        db = get_mongodb()
        print(f"Connected to database: {db.name}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")


from configs import settings
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from loggers.logapp import logger
from dataclasses import dataclass
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Optional, ClassVar

@dataclass
class MongoDBConnections:
    # Instance variables
    COLLECTION: Collection
    DOCUMENT: Collection
    CHAT_HISTORY: Collection
    USERS: Collection
    GROUPS: Collection
    DATABASE: Database

    # Class variable for singleton instance
    _instance: ClassVar[Optional['MongoDBConnections']] = None

    def __new__(cls, *args, **kwargs):
        """
        Create a new instance if one doesn't exist, otherwise return the existing instance.
        This method is called before __init__ when creating a new object.
        """
        if cls._instance is None:
            # Initialize the connection if this is the first instantiation
            mongo_db = MongoDBConnections.get_mongodb()

            mv_collection = settings.MONGODB_CB_COLLECTION
            docs = settings.MONGODB_CB_DOCS
            chat_history = settings.MONGODB_CB_HISTORY
            groups = settings.MONGODB_CB_GROUPS
            users = settings.MONGODB_CB_USERS

            # LOGGER.debug(f"MONGO URL: {os.getenv('MONGO_DB_URL')}")
            logger.debug(f"MONGODB: {settings.MONGO_DB}, collections: {mv_collection}, docs: {docs}, history: {chat_history}, groups: {groups}, users: {users}")

            # Create instance using super().__new__
            instance = super().__new__(cls)

            # Set up attributes directly
            instance.COLLECTION = mongo_db[mv_collection]
            instance.DOCUMENT = mongo_db[docs]
            instance.CHAT_HISTORY = mongo_db[chat_history]
            instance.USERS = mongo_db[users]
            instance.GROUPS = mongo_db[groups]
            instance.DATABASE = mongo_db

            cls._instance = instance        
        return cls._instance
    @staticmethod
    def get_mongodb():
        """
        Establish connection to MongoDB and return database instance.

        Returns:
            Database: MongoDB database instance

        Raises:
            ValueError: If MONGO_URL environment variable is not set
        """
        mongo_url = settings.MONGO_URL
        if not mongo_url:
            raise ValueError("MONGO_URL environment variable is required")

        client = MongoClient(mongo_url)
        db = client[settings.MONGO_DB]
        return db

    def __init__(self):
        """
        No-op init since we handle initialization in __new__
        """
        pass

def init_mongo_db() -> MongoDBConnections:
    """
    Factory function to initialize MongoDB connections.

    Returns:
        MongoDBConnections: Dataclass containing MongoDB collections
    """
    return MongoDBConnections()