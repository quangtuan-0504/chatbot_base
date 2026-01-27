from collections import defaultdict
from typing import Tuple, List, Dict
from pymilvus.exceptions import MilvusException
from pymilvus import MilvusClient
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from loggers.logapp import logger
from configs import settings


def find_overlap(prev: str, current: str) -> int:
    """Find the maximum overlap between the end of prev and the start of current."""
    for overlap in range(min(len(prev), len(current)), 0, -1):
        if prev[-overlap:] == current[:overlap]:
            return overlap
    return 0

def merge_strings(texts: List[str]) -> str:
    """Merge a list of strings, removing overlapping parts between adjacent strings."""
    if not texts:
        return ""

    result = texts[0]

    for i in range(1, len(texts)):
        overlap = find_overlap(result, texts[i])
        result += texts[i][overlap:]

    return result

def merge_document_texts(doc_text_map: Dict[str, List[str]]) -> str:
    """Merge text chunks from multiple documents with document attribution."""
    result = []

    for file_name, text_chunks in doc_text_map.items():
        merged_text = merge_strings(text_chunks)
        attribution = f"\nThe above information is taken from file: {file_name}\n\n"
        result.append(merged_text + attribution)

    return "".join(result)
def vicinity_search(
    client: MilvusClient,
    query_vector: List[float],
    collection_name: str,
    limit: int = 3,
    file_ids: List[str] = None,
    metric_type: str = "COSINE",
    offset: int = 0,
    upper_bound: int = 1,
    lower_bound: int = 1
) -> Tuple[str, List]:
    """
    Search for documents in the vector store and retrieve surrounding text chunks.
    """
    if not collection_name.startswith(settings.PREFIX_COLLECTION_NAME):
        collection_name = settings.PREFIX_COLLECTION_NAME+collection_name
    file_ids = file_ids or []

    try:
        # Check if collection exists and has data
        if not client.has_collection(collection_name):
            logger.warning(f"Collection {collection_name} does not exist")
            return "", [], []

        # Get collection statistics
        # stats = client.get_collection_stats(collection_name)
        # row_count = stats.get('row_count', 0)

        # if row_count == 0:
        #     logger.warning(f"Collection {collection_name} is empty")
        #     return "", [], []

        # Ensure collection is loaded
        client.load_collection(collection_name)

        # Set up search filter if file IDs are provided
        expr = "file_id in {list_file}" if file_ids else None
        filter_params = {"list_file": file_ids} if file_ids else None

        # Search for relevant chunks
        search_results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            limit=limit,
            filter=expr,
            filter_params=filter_params,
            output_fields=["text", "file_name", "file_id", "chunk_index_in_file"],
            search_params={
                "metric_type": metric_type,
                "offset": offset,
            }
        )

    except MilvusException as e: 
        logger.error(f"Milvus Error: {str(e)}")
        return "", [], []
    except Exception as e:
        logger.error(f"Unknown error: {str(e)}")
        raise e

    # Rest of your code remains the same...
    logger.debug(f"Found {len(search_results)} results in vector search")

    # Process search results
    relevant_files = []
    lst_img = []
    lst_img_unique = []
    document_chunks = defaultdict(list)

    for hits_group in search_results:
        for hit in hits_group:
            # Get chunk information
            chunk_index = hit['entity']['chunk_index_in_file']
            file_id = hit["entity"]["file_id"]
            file_name = hit["entity"]["file_name"]

            # Calculate vicinity range
            vicinity_indices = (
                [chunk_index - i for i in range(lower_bound, 0, -1)] +
                [chunk_index + i for i in range(0, upper_bound + 1)]
            )

            # Query for chunks in vicinity
            vicinity_filter = f'file_id == "{file_id}" && chunk_index_in_file in {vicinity_indices}'
            vicinity_results = client.query(
                collection_name=collection_name,
                filter=vicinity_filter,
                output_fields=["text", "file_name", "file_id", "chunk_index_in_file", "lst_img_of_chunks"],
            )

            # Add chunks to document map
            for vicinity_chunk in vicinity_results:
                document_chunks[file_name].append(vicinity_chunk['text'])
                lst_img.extend(vicinity_chunk['lst_img_of_chunks'])
            # Get unique image
            for path_img in lst_img:
                if path_img not in lst_img_unique:
                    lst_img_unique.append(path_img)

            # Track unique files
            if not any(file['file_id'] == file_id for file in relevant_files):
                relevant_files.append({
                    'file_name': file_name,
                    'file_id': file_id
                })

    # Merge text chunks
    merged_text = merge_document_texts(document_chunks)

    return merged_text, relevant_files, lst_img_unique
 