from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict, List
from dotenv import load_dotenv
from dotenv import find_dotenv
import os
env_file = find_dotenv()
load_dotenv(env_file)

# https://fastapi.tiangolo.com/advanced/settings/
# fixme: https://grok.com/chat/1bdaadba-9fef-4d58-880e-980897be0a97
#        https://grok.com/chat/6c31a7d1-653e-4b70-bb33-daaca8bc9b53
class Settings(BaseSettings):
    """Configuration settings for Milvus indexing and searchers.
    """
    # ignored if .env file is not set
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # extra="ignore"
    )


    app_name: str = "Chatbot Pro"
    # Admin account
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@namabank.com.vn")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MILVUS_TYPE: str = "DOCKER" # "CLOUD" OR LOCAL CONTAINER : "DOCKER"
    MILVUS_DB: str = "chatbottuan_v3" # IF USE CONTAINER LOCAL , PLEASE SET DB(CLUSTER) NAME
    MILVUS_ENDPOINT: str = os.getenv("MILVUS_ENDPOINT")
    MILVUS_TOKEN: str = os.getenv("MILVUS_TOKEN")
    MILVUS_HOST: str = os.getenv("MILVUS_HOST")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT")
    PREFIX_COLLECTION_NAME: str = "hello_"

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    ACCESS_KEY_MINIO: str = os.getenv("ACCESS_KEY_MINIO")
    SECRET_KEY_MINIO: str = os.getenv("SECRET_KEY_MINIO")
    BUCKET_NAME: str = "chatbottuan-v3"
    UPLOAD_FOLDER: str = "resources/documents" # folder in bucket to save file upload
    DOCUMENT_IMAGES: str = "resources/images" # folder in bucket to save images of file

    MONGO_URL: str = os.getenv("MONGO_URL")
    MONGO_DB: str = "chatbottuan-v3"
    MONGO_COLLECTION: List = [
        "users",
        "groups",
        "user_group",
        "chats",
        "collections",
        "user_collection",
        "documents",
    ]

    MARKER_PDF_URL: str = os.getenv("MARKER_PDF_URL", "10.18.27.59:8060")

    # RAG parameters
    RAG_MAX_COMPLETION_TOKENS: int = int(os.getenv("RAG_MAX_COMPLETION_TOKENS", 500)) # số token dành cho câu trả lời
    RAG_SEARCH_LIMIT: int = int(os.getenv("RAG_SEARCH_LIMIT", 3)) # số chunk lấy ra khi search Milvus

    # Chunking parameters
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 600)) # pdf, docx
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    XLSX_CHUNK_SIZE: int = int(os.getenv("XLSX_CHUNK_SIZE", 1000)) # xlsx, txt, doc
 
    DEVICE: int = 0

    # Structured configuration for chat and embedding models
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    chat_models: List[Dict[str, Any]] = [
        {
            "name": "gpt-6-luna", # Unique name for the model
            "provider": "openai-api", # "vllm" or "openai-api"
            "client": "openai-client",
            "type_model": "llm",
            "path": "",
            "base_url": "",
            "api_key": openai_api_key,
        },
        # {
        #     "name": "aya-expanse-8b",
        #     "provider": "vllm",
        #     "client": "openai-client",
        #     "type_model": "llm",
        #     "path": "/LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit",
        #     "base_url": "http://10.18.27.59:8000/v1",
        #     "api_key": os.getenv("VLLM_API_KEY_aya_expanse_8b"),
        # },
        # {
        #     "name": "qwen3-vl:2b",
        #     "provider": "ollama",
        #     "client": "openai-client",
        #     "type_model": "vlm",
        #     "path": "",
        #     "base_url": "http://10.18.27.59:8025/v1",
        #     "api_key": "",
        # }
    ]

    # Configuration for indexing
    embedding_model: Dict[str, Any] = {
        # "name": "BAAI/bge-m3",
        # "provider": "vllm",
        # "client": "openai-client",
        # "type_model": "vlm",
        # "path": "/LLM/EmbeddingModels/BAAI/bge-m3",
        # "base_url": "http://10.18.27.59:8001/v1",
        # "api_key": "",  # Optional, if using vLLM or other providers
        # "dim": 1024,  # Dimension of the embedding vector
        "name": "text-embedding-3-small",
        "provider": "openai-api",
        "client": "openai-client",
        "type_model": "vlm",
        "path": "",
        "base_url": "",
        "api_key": openai_api_key,  # Optional, if using vLLM or other providers
        "dim": 1536,  # Dimension of the embedding vector
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
