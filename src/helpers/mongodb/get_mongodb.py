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
    # Class variable for singleton instance, this is a attribute of this class.
    _instance: ClassVar[Optional['MongoDBConnections']] = None

    def __new__(cls, *args, **kwargs):
        """
        Create a new instance if one doesn't exist, otherwise return the existing instance.
        This method is called before __init__ when creating a new object.
        """
        if cls._instance is None:
            # Initialize the connection if this is the first instantiation
            mongo_db = MongoDBConnections.get_mongodb()

            logger.debug(f"MONGODB: {settings.MONGO_DB}, collections: {settings.MONGO_COLLECTION}")

            # Create instance using super().__new__
            instance = super().__new__(cls)

            # Dynamically (linh động) create collection attributes from settings
            for collection_name in settings.MONGO_COLLECTION:
                setattr(instance, collection_name.upper(), mongo_db[collection_name])
            
            # Set database reference
            instance.DATABASE = mongo_db

            # update _instance attribute's value, this time, _instance attribute's value is MongoDBConnections obj with attributes: _instance, DATABASE, and collection attributes
            cls._instance = instance        
        return cls._instance
        # chạy xong hàm này thì ta đã khởi tạo, đã có một đối tượng với các thuộc tính được thiết lập như những gì đã chạy ở trên.
        # giả sử ta tạo obj của lớp này lần đầu tiên
        # giả sử tạo tại obj của lớp này lần 2
        # khi mình tạo 1 obj thuộc lớp này
        # mg_db = MongoDBConnections() thì cls._instance được trả về sẽ gán vào obj mg_db.

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