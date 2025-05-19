from pymongo import MongoClient
from dotenv import load_dotenv
from dotenv import find_dotenv
from src.config.load_config import config
import os

env_file = find_dotenv()
# print(env_file)
load_dotenv(env_file)


def get_mongoDB():
    MONGO_URL = os.getenv("MONGO_URL")
    MONGO_DB = config["MONGO_DB"]
    # print(MONGO_URL)
    client = MongoClient(MONGO_URL)
    # print(client)
    db =  client[MONGO_DB]
    return db

if __name__ == "__main__":
    db = get_mongoDB()
    print(db)