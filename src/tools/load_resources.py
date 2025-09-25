from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from loggers.logapp import logger
from configs import settings
from helpers.mongodb.get_mongodb import  init_mongo_db
from helpers.milvus.milvus import get_milvus_connection
from helpers.minio import minio_client
from tools.intergrations.collection_tools import CollectionTool
from tools.intergrations.chat_tools import ChatTool
from tools.intergrations.document_tools import DocumentTool
from tools.intergrations.user_tools import UserTool
from tools.intergrations.group_tools import GroupTool
from tools.intergrations.minio_tools import ensure_bucket_exists
from utils.get_list_model_by_provider import get_list_model_by_provider


from tools.rag.indexing_milvus import  IndexingMilvusOriVLLM
from tools.rag.rag import ChatbotRAGvLLM
from typing import Dict
from openai import OpenAI


def load_resource()-> Dict:
    """Load necessary resources (MongoDB, Milvus, and models)."""
    resources = {}

    # Load MongoDB
    try:
        mongodb = init_mongo_db()
        resources["mongoDB"] = mongodb
        resources["collection_tool"] = CollectionTool(mongodb=mongodb)
        resources["document_tool"] = DocumentTool(mongodb=mongodb)
        resources["chat_tool"] = ChatTool(mongodb=mongodb)
        resources["user_tool"] = UserTool(mongodb=mongodb)
        resources["group_tool"] = GroupTool(mongodb=mongodb)

        # Create admin user if not exists
        try:
            resources["user_tool"].create_admin_user(
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                username=settings.ADMIN_USERNAME,
                name="System Administrator"
            )
        except Exception as admin_error:
            logger.error(f"Failed to create admin user: {str(admin_error)}")

        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    
    # Load Minio
    try:
        resources["minio_client"] = minio_client
        ensure_bucket_exists(minio_client=minio_client, bucket_name=settings.BUCKET_NAME)
        logger.info("Minio connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to Minio: {str(e)}")
        raise

    # Load Milvus
    try:
        milvus_client = get_milvus_connection()
        logger.info("Milvus connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {str(e)}")
        raise
    

    # Get client openai-api
    if any(model["provider"] == "openai-api" for model in settings.chat_models + [settings.embedding_model]):
        openai_client = OpenAI(
            api_key=settings.openai_api_key,
        )
    else:
        openai_client = None
        logger.warning("No use model from openAI, some features may not work.")
    
    # Load client embedding model
    embedding_model = settings.embedding_model
    try:
        if embedding_model["provider"] == "openai-api":
            openai_emb_client = openai_client
            embedding_model_name_or_path = embedding_model["name"]
        elif embedding_model["provider"] == "vllm":
            openai_emb_client = OpenAI(
                api_key=embedding_model["api_key"],
                base_url=embedding_model["base_url"],
            )
            embedding_model_name_or_path = embedding_model["path"]
        else:
            raise ValueError(f"Unsupported embedding model provider: {embedding_model['provider']}")
        
        if embedding_model['provider'] in ["openai-api", "vllm"]:
            indexing = IndexingMilvusOriVLLM(
                milvus_client = milvus_client,
                openai_client = openai_emb_client,
                embedding_model_name_or_path = embedding_model_name_or_path,
            )
        elif embedding_model['provider'] == "huggingface-transformers":
            # indexing = IndexingMilvus(...)
            pass  # Placeholder for Hugging Face Transformers indexing
        resources["indexing"] = indexing
        logger.info("IndexingMilvusOriVLLM loaded.")
    except Exception as e:
        logger.error(f"Failed to initialize IndexingMilvusOriVLLM: {str(e)}")
        raise
    
    # Load chat models
    for model in settings.chat_models:
        try:
            name = model["name"]
            provider = model["provider"]
            api_key = model["api_key"]
            base_url = model.get("base_url", "")
            path = model.get("path", "")
        
            if provider == "openai-api":
                client_chat_model = openai_client
                chat_model_name = name
            elif provider == "vllm":
                client_chat_model = OpenAI(api_key=api_key, base_url=base_url)
                chat_model_name = path
            else:
                logger.warning(f"Unsupported provider {provider} for model {name}")
                continue
            
            # Initialize the ChatbotRAGvLLM with the loaded model
            if provider in ["openai-api", "vllm"]:
                logger.info(f"Loading chat model {name} from {provider}...")
                resources[name] = ChatbotRAGvLLM(
                    chat_model_name = chat_model_name,
                    embedding_model_name = embedding_model_name_or_path,
                    client_chat_model = client_chat_model,
                    client_embedding_model = openai_emb_client,
                    milvus_client = milvus_client,
                )
            elif provider == "huggingface-transformers":
                # resources[name] = ChatbotRAGHuggingFace(...)
                pass
            logger.info(f"Chat model {name} loaded.")
        except Exception as e:
            logger.error(f"Failed to load chat model {name}: {str(e)}")
            continue  # Skip failed models to allow partial loading

    return resources

resource = {}
provider_model = {}
@asynccontextmanager
async def resourcelifespan(app: FastAPI):
    """Lifespan context manager for FastAPI to load and clean up resources."""
    logger.info("Loading resources...")
    try:
        resource.update(load_resource())
        provider_model.update(get_list_model_by_provider())
        logger.info(f"Resources loaded: {list(resource.keys())}")
        yield
    finally:
        logger.info("Cleaning up resources...")
        resource.clear()
        logger.info("Resources cleared.")