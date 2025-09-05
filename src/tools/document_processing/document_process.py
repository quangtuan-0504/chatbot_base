import time
from src.helpers.milvus import Vectorstores
from src.document_loaders.documents import load_document
from src.utils import logSetup
import tempfile
import os
LOGGER = logSetup()



def process_file(
        file_data : dict,
        files_collection,
        vectorstores: Vectorstores
    ):
    """
    Process a file based on its type and add it to the Milvus vectorstore.

    Args:
        file_data (dict): Dictionary containing file metadata
        vectorstores (Vectorstores): Vectorstore manager instance
        embeddings: Embedding model to use
        text_splitter: Document splitter to use
        batch_size (int): Batch size for adding documents to vectorstore
    """
    file_id = file_data['_id']
    file_type = file_data['file_type']
    file_path = file_data['file_path'] # relative path in minIO (object name)
    file_name = file_data['file_name']
    collection_id = file_data.get('collection_id')

    LOGGER.info(f"Processing file {file_id} of type {file_type}")
    try:
        # Update status to processing
        files_collection.update_one(
            {'_id': file_id},
            {'$set': {'status': 'processing', 'processing_started': int(time.time())}}
        )

        split_documents = load_document(
            file_path = file_path,
            collection_id = collection_id,
            file_id = str(file_id)
        )


        # Add file_id to metadata for each document
        for doc in split_documents:
            if not hasattr(doc, 'metadata'):
                doc.metadata = {}
            doc.metadata['file_id'] = str(file_id)
            doc.metadata['file_name'] = file_name
            doc.metadata['source'] = file_path

        # LOGGER.debug(str(documents))

        total_docs = vectorstores.add_document(
            document_chunks=split_documents, collection_name=collection_id)
        # Update status to completed
        files_collection.update_one(
            {'_id': file_id},
            {
                '$set': {
                    'status': 'completed',
                    'processing_completed': int(time.time()),
                    'result': f"Successfully processed {file_type} file. Added {total_docs} document chunks to vectorstore.",
                    'doc_chunks_count': total_docs
                }
            }
        )
        LOGGER.info(f"Successfully processed {file_type} file. Added {total_docs} document chunks to vectorstore.",)
        return True

    except Exception as e:
        # Update status to error and increment retry counter
        LOGGER.error(f"Error processing file {file_id}: {str(e)}")
        files_collection.update_one(
            {'_id': file_id},
            {
                '$set': {
                    'status': 'error',
                    'error_message': str(e),
                    'error_time': int(time.time())
                },
                '$inc': {'process_attempts': 1}
            }
        )
        return False