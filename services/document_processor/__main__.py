# processor.py - Worker service to process files from the queue
import time
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from pymongo import ASCENDING
import threading
from openai import OpenAI

from src.tools.document_processing.document_process import process_file
from src.helpers.mongodb.get_mongodb import MongoDBConnections
from src.helpers.milvus.milvus import get_milvus_connection
from src.helpers.minio import minio_client
from src.loggers.logapp import logger
from src.tools.rag.indexing_milvus import IndexingMilvusOri
from src.configs import settings




mongodb = MongoDBConnections()
files_collection = mongodb.DOCUMENTS
# Create index for faster queries
files_collection.create_index([("status", ASCENDING), ("created_at", ASCENDING), ("collection_id", ASCENDING) ])

# Load Milvus
try:
    milvus_client = get_milvus_connection()
    logger.info("Milvus connection established.")
except Exception as e:
    logger.error(f"Failed to connect to Milvus: {str(e)}")
    raise

# Get client openai-api, if use any model from openai
if any(model["provider"] == "openai-api" for model in settings.chat_models + [settings.embedding_model]):
    openai_client = OpenAI(
        api_key=settings.openai_api_key
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
        logger.info("Use provider openai-api for embedding documents")
    elif embedding_model["provider"] in ("vllm", "ollama"):
        openai_emb_client = OpenAI(
            api_key=embedding_model["api_key"],
            base_url=embedding_model["base_url"],
        )
        embedding_model_name_or_path = embedding_model["path"]
    else:
        raise ValueError(f"Unsupported embedding model provider: {embedding_model['provider']}")

    if embedding_model['provider'] in ["openai-api", "vllm", "ollama"]:
        indexing = IndexingMilvusOri(
            milvus_client = milvus_client,
            openai_client = openai_emb_client,
            embedding_model_name_or_path = embedding_model_name_or_path,
        )
    elif embedding_model['provider'] == "huggingface-transformers":
        # indexing = IndexingMilvus(...)
        pass  # Placeholder for Hugging Face Transformers indexing
    logger.info("IndexingMilvusOri loaded.")
except Exception as e:
    logger.error(f"Failed to initialize IndexingMilvusOri: {str(e)}")
    raise

# # test connnect emb model vllm
# response = openai_emb_client.embeddings.create(
#     input="how are you ?",
#     model=embedding_model_name_or_path
# )

# print(response.data[0].embedding)

# Configuration
MAX_PROCESSING_TIME = int(os.getenv("MAX_PROCESSING_TIME", 3600))  # seconds; a large PDF through Marker can take several minutes, resetting it earlier makes another thread index it twice
MAX_RETRY_ATTEMPTS = 3
POLLING_INTERVAL = 10  # seconds
NUM_WORKER_THREADS = 3

def reset_stalled_jobs():
    """Reset any jobs that have been processing for too long."""
    stall_threshold = int(time.time()) - MAX_PROCESSING_TIME

    stalled_files = files_collection.find(
        {
            'status': 'processing',
            'processing_started': {'$lt': stall_threshold}
        }
    )

    for file in stalled_files:
        logger.warning(f"Resetting stalled job: {file['_id']}")
        files_collection.update_one(
            {'_id': file['_id']},
            {
                '$set': {'status': 'pending'},
                '$inc': {'process_attempts': 1}
            }
        )

def worker_thread():
    """Worker thread to continuously process files from the queue."""
    while True:
        try:
            # Find a pending file to process
            pending_file = files_collection.find_one_and_update(
                {
                    'status': 'pending',
                    'process_attempts': {'$lt': MAX_RETRY_ATTEMPTS}
                },
                {'$set': {'status': 'reserved'}},
                sort=[('created_at', ASCENDING)]
            )

            if pending_file:
                logger.info(f"Worker picked up file: {pending_file['_id']}")
                process_file(
                    file_data = pending_file,
                    files_collection = files_collection,
                    indexing = indexing
                )
            else:
                # No files to process, sleep before checking again
                time.sleep(POLLING_INTERVAL)

            # Check for stalled jobs periodically
            reset_stalled_jobs()

        except Exception as e:
            logger.error(f"Worker thread error: {str(e)}")
            time.sleep(POLLING_INTERVAL)

def start_worker_service():
    """Start the worker service with multiple threads."""
    logger.info(f"Starting file processor worker service with {NUM_WORKER_THREADS} threads")

    # Create worker threads
    threads = []
    for i in range(NUM_WORKER_THREADS):
        thread = threading.Thread(target=worker_thread)
        thread.daemon = True
        threads.append(thread)
        thread.start()
        logger.info(f"Started worker thread {i+1}")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
            # logger.info("Worker service heartbeat")
    except KeyboardInterrupt:
        logger.info("Worker service shutting down")

if __name__ == "__main__":
    start_worker_service()