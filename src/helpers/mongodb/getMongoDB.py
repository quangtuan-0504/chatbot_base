import os
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv

from configs import settings

# Load environment variables
load_dotenv(find_dotenv())


def get_mongodb():
    """
    Establish connection to MongoDB and return database instance.
    
    Returns:
        Database: MongoDB database instance
        
    Raises:
        ValueError: If MONGO_URL environment variable is not set
    """
    mongo_url = os.getenv("MONGO_URL")
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