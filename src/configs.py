from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List
from dotenv import load_dotenv
from dotenv import find_dotenv
import os
env_file = find_dotenv()
load_dotenv(env_file)

# https://fastapi.tiangolo.com/advanced/settings/
class Settings(BaseSettings):
    """Configuration settings for Milvus indexing and searchers.
       fixme: https://grok.com/chat/1bdaadba-9fef-4d58-880e-980897be0a97
       https://grok.com/chat/6c31a7d1-653e-4b70-bb33-daaca8bc9b53
    """
    # ignored if .env file is not set
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # extra="ignore"
    )


    app_name: str = "Chatbot Pro"

    MILVUS_TYPE: str = "DOCKER" # "CLOUD" OR LOCAL CONTAINER : "DOCKER"
    MILVUS_DB: str = "VECTORDB_TEST" # IF USE CONTAINER LOCAL , PLEASE SET DB(CLUSTER) NAME
    MILVUS_ENDPOINT: str = os.getenv("MILVUS_ENDPOINT")
    MILVUS_TOKEN: str = os.getenv("MILVUS_TOKEN")
    MILVUS_HOST: str = os.getenv("MILVUS_HOST")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT")
    PREFIX_COLLECTION_NAME: str = "hello_"

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    ACCESS_KEY: str = os.getenv("ACCESS_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    BUCKET_NAME: str = os.getenv("BUCKET_NAME")
    UPLOAD_FOLDER: str = "resources/documents" # folder in bucket to save file upload
    DOCUMENT_IMAGES: str = "resources/images" # folder in bucket to save images of file

    MARKER_PDF_URL: str = "10.18.27.59:8060"

 


    MONGO_URL: str = os.getenv("MONGO_URL")
    MONGO_DB: str = "chatbotbase"
    MONGO_COLLECTION: List = [
        "users",
        "chats",
        "collections",
        "user_collection",
        "documents",
        "authorizations",
        "user_authorization"
    ]
 

    PATH_SAVE_FILE_UPLOAD: str = "./FOLDER_FILE_UPLOAD"
    PATH_SAVE_IMG_OF_FILE: str = "./FOLDER_SAVE_IMG"

    DEVICE: int = 0

    # Structured configuration for chat and embedding models
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    chat_models: List[Dict[str, any]] = [
        # {
        #     "name": "gpt-4o-mini",
        #     "provider": "openai-api", # "vllm" or "openai-api"
        #     "path": "",
        #     "base_url": "",
        #     "api_key": "",
        # },
        {
            "name": "aya-expanse-8b",
            "provider": "vllm",
            "path": "/LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit",
            "base_url": "http://localhost:8000/v1",
            "api_key": os.getenv("VLLM_API_KEY_aya_expanse_8b"),
        }
    ]

    # Configuration for indexing
    embedding_model: Dict[str, any] = {
        "name": "BAAI/bge-m3",
        "provider": "vllm",
        "path": "/LLM/EmbeddingModels/BAAI/bge-m3",
        "base_url": "http://localhost:8001/v1",
        "api_key": "",  # Optional, if using vLLM or other providers
        "dim": 1024,  # Dimension of the embedding vector
    }

    batch_size: int = 500
    nprobe: int = 10
    limit_per_qr: int = 50
    nlist: int = 512  # Number of clusters for IVF index

    def __init__(self):
        super().__init__()
        # Validate API keys
        if not self.openai_api_key and any(model["provider"] == "openai-api" for model in self.chat_models + [self.embedding_model]):
            raise ValueError("OPENAI_API_KEY is required for OpenAI models")
        # if any(model["provider"] == "vllm" for model in self.chat_models):
        #     raise ValueError("VLLM_API_KEY is required for vLLM models")

settings = Settings()

if __name__ == "__main__":
    print(settings)