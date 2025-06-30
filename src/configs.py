from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Union, Dict, List
from pymilvus import DataType, Function, FunctionType



# https://fastapi.tiangolo.com/advanced/settings/
class Settings(BaseSettings):
    """Configuration settings for Milvus indexing and searchers.
       fixme: https://grok.com/chat/1bdaadba-9fef-4d58-880e-980897be0a97
    """
    # ignored if .env file is not set
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8") # extra="ignore"

    app_name: str = "Chatbot Pro"
    MILVUS_TYPE: str = "CLOUD" # "CLOUD" OR LOCAL CONTAINER : "DOCKER"
    MILVUS_DB: str = "DB_milvus" # IF USE CONTAINER LOCAL , PLEASE SET DB(CLUSTER) NAME

    MONGO_DB: str = "chatbotbase"
    PATH_SAVE_FILE_UPLOAD: str = "./FOLDER_FILE_UPLOAD"
    PATH_SAVE_IMG_OF_FILE: str = "./FOLDER_SAVE_IMG"

    DEVICE: int = 0

    # MILVUS, QDRANT, ...
    SERVICE_VECTOR_STORE:str = "MILVUS"

    chat_model: List[dict] = [
        {
            "name": "gpt-4o-mini",
            "provider": "openai-api",
            "path": "",
            "type": "chat"
        },
        {
            "name": "gpt-4o",
            "provider": "openai-api",
            "path": "",
            "type": "chat"
        },
        {
            "name": "aya-expanse-8b",
            "provider": "huggingface-transformers",
            "path": "/home/tuanndq/test_chatbot/chatbot/LLM/LLMs/CohereForAI/aya-expanse-8b",
            "type": "chat"
        },
        {
            "name": "bloom-1b7",
            "provider": "huggingface-transformers",
            "path": "/home/tuanndq/test_chatbot/download_model/model/chat_models/bigscience/bloom-1b7",
            "type": "chat"
        },
        {
            "name": "aya-expanse-8b",
            "provider": "vllm",
            "path": "/home/tuanndq/test_chatbot/chatbot/LLM/LLMs/CohereForAI/aya-expanse-8b",
            "type": "chat"
        },
        {
            "name": "bloom-1b7",
            "provider": "vllm",
            "path": "/home/tuanndq/test_chatbot/download_model/model/chat_models/bigscience/bloom-1b7",
            "type": "chat"
        }
    ]

    embedding_model: List[dict] = [
        {
            "name": "text-embedding-3-small",
            "provider": "openai-api",
            "path": "",
            "type": "embedding"
        },
        {
            "name": "bge-m3-model",
            "provider": "huggingface-transformers",
            "path": "/home/tuanndq/test_chatbot/download_model/model/embedding_models/bge/bge-m3-model",
            "type": "embedding"
        },
        {
            "name": "bge-m3-model",
            "provider": "vllm",
            "path": "/home/tuanndq/test_chatbot/download_model/model/embedding_models/bge/bge-m3-model",
            "type": "embedding"
        }
    ]


    batch_size: int = 500
    nprobe: int = 10
    limit_per_qr: int = 50

settings = Settings()

if __name__ == "__main__":
    print(settings)