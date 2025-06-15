from fastapi import FastAPI
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from dotenv import find_dotenv
import os


import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from helpers.mongoDB.getMongoDB import  get_mongoDB
from config.load_config import config
from tools.indexingMilvus import  IndexingMilvusOriVLLM
from tools.retrievalAndGeneration import ChatbotRAGvLLM
from pymilvus import connections, db
from typing import Dict


env_file = find_dotenv()
load_dotenv(env_file)

def load_resource()-> dict:
    print("load resource !")
    re = {}

    re["mongoDB"] = get_mongoDB()
    
    if config["SERVICE_VECTOR_STORE"] == "MILVUS":
        conn = connections.connect( 
            host= os.getenv("MILVUS_HOST"),
            post = os.getenv("MILVUS_PORT")
        )
        db_name = config["MILVUS_DB"]
        if db_name not in db.list_database():
            database = db.create_database(db_name)
        indexing = IndexingMilvusOriVLLM(embedding_model_name="/LLM/EmbeddingModels/BAAI/bge-m3")
        # indexing = None # test mà ko cần load model
        re["indexing"] = indexing
        print("indexing loaded")
    elif config["SERVICE_VECTOR_STORE"] == "QDRANT":
        pass
   
    if config['vllm']['aya_expand_8b_vllm']:        
        re["chatbot_aya_expanse_8b_vllm"] = ChatbotRAGvLLM(chat_model_name= "/LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit",
                                                           embedding_model_name="/LLM/EmbeddingModels/BAAI/bge-m3")
        print("aya expanse 8b vllm is loaded")

    return re

resource = {}

# will be loaded on app startup
@asynccontextmanager
async def resourcelifespan(app: FastAPI):
    # Load the ML model
    resource.update(load_resource())
    print(resource)
    yield
    # Clean up the ML models and release the resources
    resource.clear()