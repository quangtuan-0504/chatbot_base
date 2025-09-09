import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.mongodb.get_mongodb import MongoDBConnections
from tools.rag.indexing_milvus import IndexingMilvusOriVLLM
from configs import settings
from loggers.logapp import logger
from src.utils.timezone_utils import get_gmt7_datetime_for_db


class ChatTool:
    def __init__(self, mongodb: MongoDBConnections = None):
        self.mongodb = mongodb

 