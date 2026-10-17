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
    RAG_SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", 0.3)) # bỏ chunk có cosine similarity thấp hơn ngưỡng
    RAG_MAX_IMAGES: int = int(os.getenv("RAG_MAX_IMAGES", 5)) # số ảnh tối đa trả về, ưu tiên ảnh của chunk tìm thấy trực tiếp
    RAG_REWRITE_HISTORY_TURNS: int = int(os.getenv("RAG_REWRITE_HISTORY_TURNS", 3)) # số lượt hội thoại (user + assistant) dùng để viết lại câu hỏi trước khi search, 0 = tắt

    # Hybrid search (dense + BM25), trộn bằng RRF
    RAG_HYBRID_ENABLED: bool = os.getenv("RAG_HYBRID_ENABLED", "true").lower() == "true" # false = chỉ dùng dense
    RAG_HYBRID_CANDIDATES: int = int(os.getenv("RAG_HYBRID_CANDIDATES", 10)) # số kết quả lấy từ mỗi nhánh trước khi trộn
    RAG_RRF_K: int = int(os.getenv("RAG_RRF_K", 60)) # hằng số k của RRF: score = sum(1 / (k + rank))
    RAG_BM25_MIN_SCORE: float = float(os.getenv("RAG_BM25_MIN_SCORE", 0.0)) # bỏ kết quả BM25 có điểm thấp hơn ngưỡng
    RAG_BM25_MIN_TERM_RATIO: float = float(os.getenv("RAG_BM25_MIN_TERM_RATIO", 0.5)) # tỉ lệ từ (âm tiết) của câu hỏi tối thiểu phải có trong chunk BM25; tiếng Việt trùng 1 âm tiết rất dễ nên cần lọc
    HNSW_ENABLED: bool = os.getenv("HNSW_ENABLED", "false").lower() == "true" # true = collection mới dùng HNSW thay cho IVF_FLAT
    VI_STOPWORDS: List[str] = [
        "là", "của", "và", "các", "có", "được", "cho", "này", "thì", "những", "một", "với", "trong",
        "để", "khi", "đã", "sẽ", "đang", "cũng", "như", "từ", "theo", "về", "tại", "bị", "do", "nên",
        "nếu", "mà", "hay", "hoặc", "nào", "gì", "ở", "ra", "vào", "lên", "đó", "kia", "ấy", "rằng",
        # từ đệm thường gặp trong câu hỏi
        "tôi", "bạn", "mình", "hỏi", "xin", "giúp", "muốn", "biết", "thế", "vậy", "ạ", "nhé", "không",
    ]

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

    # Embedding model served by vllm (BAAI/bge-m3)
    EMBEDDING_MODEL_PATH: str = os.getenv("EMBEDDING_MODEL_PATH", "BAAI/bge-m3") # with vllm, this is the model name served by `vllm serve`
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "http://localhost:8320/v1")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "EMPTY") # vllm without --api-key accepts any value, but the OpenAI client requires one

    # Configuration for indexing
    embedding_model: Dict[str, Any] = {
        "name": "BAAI/bge-m3",
        "provider": "vllm",
        "client": "openai-client",
        "type_model": "vlm",
        "path": EMBEDDING_MODEL_PATH,
        "base_url": EMBEDDING_BASE_URL,
        "api_key": EMBEDDING_API_KEY,
        "dim": 1024,  # Dimension of the embedding vector
        # "name": "text-embedding-3-small",
        # "provider": "openai-api",
        # "client": "openai-client",
        # "type_model": "vlm",
        # "path": "",
        # "base_url": "",
        # "api_key": openai_api_key,  # Optional, if using vLLM or other providers
        # "dim": 1536,  # Dimension of the embedding vector
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
