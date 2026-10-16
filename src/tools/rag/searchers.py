import re
from typing import Tuple, List, Dict, Optional, Set
from pymilvus.exceptions import MilvusException
from pymilvus.client.types import LoadState
from pymilvus import MilvusClient
from src.loggers.logapp import logger
from src.configs import settings


# BM25 sparse vector field generated from 'text' (see indexing_milvus.build_schema_and_index)
SPARSE_FIELD = "sparse"
HIT_OUTPUT_FIELDS = ["file_name", "file_id", "chunk_index_in_file"]
STOPWORDS = frozenset(settings.VI_STOPWORDS)


class VectorSearchError(RuntimeError):
    """Raised when Milvus fails during search, so callers can tell it apart from 'no relevant documents'."""


def rrf_fuse(ranked_lists: List[List[Dict]], k: int, limit: int) -> List[Dict]:
    """Reciprocal Rank Fusion: score = sum(1 / (k + rank)) over lists, keyed by (file_id, chunk_index_in_file)."""
    scores: Dict[Tuple[str, int], float] = {}
    hits_by_key: Dict[Tuple[str, int], Dict] = {}
    for hits in ranked_lists:
        for rank, hit in enumerate(hits, start=1):
            key = (hit["entity"]["file_id"], hit["entity"]["chunk_index_in_file"])
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            hits_by_key.setdefault(key, hit)
    ranked = sorted(scores, key=scores.get, reverse=True)[:limit]
    logger.info(f"RRF fused: {[(key, round(scores[key], 4)) for key in ranked]}")
    return [hits_by_key[key] for key in ranked]

def analyze_terms(text: str) -> Set[str]:
    """Python approximation of the BM25 analyzer (standard tokenizer, lowercase, stopwords)."""
    return {term for term in re.findall(r"[^\W_]+", text.lower()) if term not in STOPWORDS}

def term_ratio(query_terms: Set[str], text: str) -> float:
    """Share of query terms present in text. Vietnamese is split into syllables, so a single shared
    syllable already gives a BM25 score; this ratio filters such accidental matches."""
    if not query_terms:
        return 0.0
    return len(query_terms & analyze_terms(text)) / len(query_terms)

def has_sparse_field(client: MilvusClient, collection_name: str) -> bool:
    """Collections created before hybrid search have no BM25 field and are searched dense-only."""
    return any(field["name"] == SPARSE_FIELD for field in client.describe_collection(collection_name)["fields"])


def find_overlap(prev: str, current: str) -> int:
    """Find the maximum overlap between the end of prev and the start of current."""
    for overlap in range(min(len(prev), len(current)), 0, -1):
        if prev[-overlap:] == current[:overlap]:
            return overlap
    return 0

def merge_chunks(chunks: List[Tuple[int, str]]) -> str:
    """Merge (chunk_index, text) pairs sorted by index.
    Only adjacent chunks share overlap; a gap between indices is marked with '...'."""
    result = ""
    prev_index, prev_text = None, ""

    for index, text in chunks:
        if prev_index is None:
            result = text
        elif index == prev_index + 1:
            result += text[find_overlap(prev_text, text):]
        else:
            result += "\n...\n" + text
        prev_index, prev_text = index, text

    return result

def merge_document_texts(documents: List[Tuple[str, List[Tuple[int, str]]]]) -> str:
    """Merge text chunks from multiple documents, each headed by its file name.
    Avoid 'Nguồn:' / 'Source:' here: chat history is cut at those markers in routers/chats.py."""
    return "\n\n".join(
        f"### Tài liệu: {file_name}\n{merge_chunks(chunks)}"
        for file_name, chunks in documents
    )

def select_images(
    hit_keys: List[Tuple[str, int]],
    images_by_chunk: Dict[Tuple[str, int], List[str]],
    max_images: int,
) -> List[str]:
    """Images of directly matched chunks first (by score), then images of vicinity chunks, deduped and capped."""
    ordered = [img for key in hit_keys for img in images_by_chunk.get(key, [])]
    ordered += [img for imgs in images_by_chunk.values() for img in imgs]
    return list(dict.fromkeys(ordered))[:max_images]

def vicinity_search(
    client: MilvusClient,
    query_vector: List[float],
    collection_name: str,
    limit: int = settings.RAG_SEARCH_LIMIT,
    file_ids: List[str] = None,
    metric_type: str = "COSINE",
    offset: int = 0,
    upper_bound: int = 1,
    lower_bound: int = 1,
    score_threshold: Optional[float] = settings.RAG_SCORE_THRESHOLD,
    max_images: int = settings.RAG_MAX_IMAGES,
    query_text: Optional[str] = None,
) -> Tuple[str, List[Dict[str, str]], List[str]]:
    """
    Search for documents in the vector store and retrieve surrounding text chunks.
    With query_text and a collection that has the BM25 field, dense and BM25 results are fused with RRF;
    otherwise the search is dense-only.
    Returns (merged context, relevant files, image paths).
    Raises VectorSearchError if Milvus fails.
    """
    if not collection_name.startswith(settings.PREFIX_COLLECTION_NAME):
        collection_name = settings.PREFIX_COLLECTION_NAME+collection_name
    file_ids = file_ids or []

    try:
        # Check if collection exists and has data
        if not client.has_collection(collection_name):
            logger.warning(f"Collection {collection_name} does not exist")
            return "", [], []

        # Ensure collection is loaded
        if client.get_load_state(collection_name)["state"] != LoadState.Loaded:
            client.load_collection(collection_name)

        hybrid = bool(settings.RAG_HYBRID_ENABLED and query_text and query_text.strip()
                      and has_sparse_field(client, collection_name))
        candidates = max(limit, settings.RAG_HYBRID_CANDIDATES) if hybrid else limit

        # Set up search filter if file IDs are provided
        expr = "file_id in {list_file}" if file_ids else None
        filter_params = {"list_file": file_ids} if file_ids else None

        # Dense search for relevant chunks
        dense_results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            anns_field="vector",
            limit=candidates,
            filter=expr,
            filter_params=filter_params,
            output_fields=HIT_OUTPUT_FIELDS,
            search_params={
                "metric_type": metric_type,
                "params": {"nprobe": settings.nprobe, "ef": max(64, candidates)},
                "offset": offset,
            }
        )

        # BM25 search on the raw query text
        sparse_results = []
        if hybrid:
            sparse_results = client.search(
                collection_name=collection_name,
                data=[query_text],
                anns_field=SPARSE_FIELD,
                limit=candidates,
                filter=expr,
                filter_params=filter_params,
                output_fields=HIT_OUTPUT_FIELDS + ["text"],
                search_params={"metric_type": "BM25", "offset": offset},
            )
    except MilvusException as e:
        logger.error(f"Milvus Error when searching {collection_name}: {str(e)}")
        raise VectorSearchError(str(e)) from e

    dense_hits = [hit for hits_group in dense_results for hit in hits_group]
    logger.info(f"Vector search scores: {[round(hit['distance'], 4) for hit in dense_hits]}")

    # COSINE / IP: higher is more similar, so drop hits below the threshold
    if score_threshold is not None and metric_type in ("COSINE", "IP"):
        dense_hits = [hit for hit in dense_hits if hit["distance"] >= score_threshold]
    logger.debug(f"Kept {len(dense_hits)} dense results after score threshold {score_threshold}")

    if hybrid:
        sparse_hits = [hit for hits_group in sparse_results for hit in hits_group]
        query_terms = analyze_terms(query_text)
        ratios = [term_ratio(query_terms, hit["entity"]["text"]) for hit in sparse_hits]
        logger.info(f"BM25 search scores (score, term ratio): "
                    f"{[(round(hit['distance'], 4), round(ratio, 2)) for hit, ratio in zip(sparse_hits, ratios)]}")
        sparse_hits = [
            hit for hit, ratio in zip(sparse_hits, ratios)
            if hit["distance"] >= settings.RAG_BM25_MIN_SCORE and ratio >= settings.RAG_BM25_MIN_TERM_RATIO
        ]
        hits = rrf_fuse([dense_hits, sparse_hits], k=settings.RAG_RRF_K, limit=limit)
    else:
        hits = dense_hits[:limit]

    if not hits:
        return "", [], []

    # Group vicinity indices by file, keeping files in order of their best hit
    files: Dict[str, Dict] = {}
    hit_keys: List[Tuple[str, int]] = []
    for hit in hits:
        entity = hit["entity"]
        chunk_index = entity["chunk_index_in_file"]
        hit_keys.append((entity["file_id"], chunk_index))
        file = files.setdefault(
            entity["file_id"],
            {"file_name": entity["file_name"], "indices": set()}
        )
        file["indices"].update(range(max(chunk_index - lower_bound, 0), chunk_index + upper_bound + 1))

    documents = []
    images_by_chunk: Dict[Tuple[str, int], List[str]] = {}
    for file_id, file in files.items():
        # One query per file for all vicinity chunks
        try:
            vicinity_results = client.query(
                collection_name=collection_name,
                filter="file_id == {file_id} && chunk_index_in_file in {indices}",
                filter_params={"file_id": file_id, "indices": sorted(file["indices"])},
                output_fields=["text", "chunk_index_in_file", "lst_img_of_chunks"],
            )
        except MilvusException as e:
            logger.error(f"Milvus Error when querying vicinity of file {file_id} in {collection_name}: {str(e)}")
            raise VectorSearchError(str(e)) from e

        # Dedupe by chunk index and sort, since query results have no guaranteed order
        chunks_by_index = {chunk["chunk_index_in_file"]: chunk for chunk in vicinity_results}
        sorted_chunks = [chunks_by_index[index] for index in sorted(chunks_by_index)]

        documents.append((
            file["file_name"],
            [(chunk["chunk_index_in_file"], chunk["text"]) for chunk in sorted_chunks]
        ))
        for chunk in sorted_chunks:
            images_by_chunk[(file_id, chunk["chunk_index_in_file"])] = chunk["lst_img_of_chunks"] or []

    relevant_files = [
        {"file_name": file["file_name"], "file_id": file_id}
        for file_id, file in files.items()
    ]

    # Merge text chunks
    merged_text = merge_document_texts(documents)

    return merged_text, relevant_files, select_images(hit_keys, images_by_chunk, max_images)
