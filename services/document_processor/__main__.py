# processor.py - Worker service to process files from the queue
import time
import os
from dotenv import load_dotenv
load_dotenv()
import logging
from pymongo import MongoClient, ASCENDING
import time 
import threading
from bson.objectid import ObjectId
from .document_process import process_file
from src.helpers.mongodb import MongoDBConnections
from src.utils import logSetup
from src.helpers.milvus import Vectorstores
logger = logSetup(logname="document")
mongodb = MongoDBConnections()
files_collection = mongodb.DOCUMENT
# Create index for faster queries
files_collection.create_index([("status", ASCENDING), ("created_at", ASCENDING), ("collectionId", ASCENDING) ])
vectorstores = Vectorstores()
# Configuration
MAX_PROCESSING_TIME = 300  # seconds
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
                    vectorstores = vectorstores
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