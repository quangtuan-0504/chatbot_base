from collections import defaultdict
from typing import Tuple, List
def merge_strings(lst)-> str:
    if not lst:
        return ""
    
    result = lst[0]  # Bắt đầu với chuỗi đầu tiên
    
    for i in range(1, len(lst)):
        current = lst[i]  # Chuỗi hiện tại
        prev = lst[i-1]   # Chuỗi trước đó
        
        # Tìm độ dài phần trùng lặp
        overlap = 0
        for j in range(len(prev), 0, -1):
            if current.startswith(prev[-j:]):
                overlap = j
                break
        
        # Thêm phần không trùng lặp của chuỗi hiện tại
        result += current[overlap:]
    
    return result
def union_overlab(dict_doc_texts : dict[str,list]) -> str: 
    total_text_retrieved = ""
    for file_name, lst_text in dict_doc_texts.items():
        text_join_of_file = merge_strings(lst_text)
        total_text_retrieved += text_join_of_file + f"\nthe above information is taken from file : {file_name}\n\n"   
    return  total_text_retrieved
def vicinity_search(
    client ,
    query_vector : list[float] ,
    collection_name : str ,
    limit : int = 5,
    file_names : list = [] ,
    metric_type : str = "COSINE",
    offset : int = 0,
    upper_bound : int = 2,
    lower_bound : int =2
) -> Tuple[str,List]:
    expr = "file_name in {list_file}" if file_names else None
    filter_params = {"list_file": file_names} if file_names else None
    res = client.search(
        collection_name = collection_name,
        data=[query_vector],
        limit=limit,
        filter=expr,
        filter_params=filter_params,
        output_fields=["text","file_name", "chunk_index_in_file"],
        search_params = {
            "metric_type": metric_type, 
            "offset": offset ,# The records to skip
            # "params": {
            #     "radius": 0.4,
            #     "range_filter": 0.6
            # }
        }
        
    )
    lst_file_relevant = []
    dic_doc_texts_relevant = defaultdict(list)
    for hits in res:
        for hit in hits:
            vicinities_range=[hit['entity']['chunk_index_in_file'] - x for x in range(lower_bound,0,-1)] \
                        + [hit['entity']['chunk_index_in_file'] + x for x in range(0,upper_bound+1)]
            file_name = hit["entity"]["file_name"]
            expr = f'file_name == "{file_name}" && chunk_index_in_file in {vicinities_range}' if vicinities_range else None # expression
            res_vicinities = client.query(
                collection_name=collection_name,
                filter=expr,
                output_fields=["text","file_name", "chunk_index_in_file"],
            )
            for vicinities in res_vicinities:
                dic_doc_texts_relevant[vicinities['file_name']].append(vicinities['text'])
                if vicinities["file_name"] not in lst_file_relevant:
                    lst_file_relevant.append(vicinities["file_name"])
    # for k,v in dic_doc_texts_relevant.items():
    #             res_retrieval += "\n".join(v) + f"\nthe above information is taken from file : {k}\n\n"
    total_text_retrieved = union_overlab(dict_doc_texts=dic_doc_texts_relevant)
    return total_text_retrieved , lst_file_relevant




from collections import defaultdict
from typing import Tuple, List, Dict
from pymilvus.exceptions import MilvusException


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
    client,
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
            LOGGER.warning(f"Collection {collection_name} does not exist")
            return "", [], []

        # Get collection statistics
        stats = client.get_collection_stats(collection_name)
        row_count = stats.get('row_count', 0)

        if row_count == 0:
            LOGGER.warning(f"Collection {collection_name} is empty")
            return "", [], []

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
        LOGGER.error(f"Milvus Error: {str(e)}")
        return "", [], []
    except Exception as e:
        LOGGER.error(f"Unknown error: {str(e)}")
        raise e

    # Rest of your code remains the same...
    LOGGER.debug(f"Found {len(search_results)} results in vector search")

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
 