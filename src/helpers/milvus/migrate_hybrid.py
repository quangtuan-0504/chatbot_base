"""Migrate chunk collections to the hybrid (dense + BM25) schema without re-embedding.

Existing rows (vector, text, metadata) are copied into a new collection built with
build_schema_and_index, which generates the BM25 'sparse' field from 'text' on insert.
The old collection is dropped and the new one renamed to the old name only when row counts match.
Run during low traffic: inserts made into a collection while it is being copied make the counts
differ, and that collection is then left untouched.

Usage (from the project root):
    python -m src.helpers.milvus.migrate_hybrid --dry-run
    python -m src.helpers.milvus.migrate_hybrid
    python -m src.helpers.milvus.migrate_hybrid --collection <collection_id>
"""
import argparse
from typing import List, Optional
from pymilvus import MilvusClient
from src.configs import settings
from src.helpers.milvus.milvus import get_milvus_connection_args
from src.loggers.logapp import logger
from src.tools.rag.indexing_milvus import build_schema_and_index
from src.tools.rag.searchers import has_sparse_field

TMP_SUFFIX = "_hybrid_tmp"


def collections_to_migrate(client: MilvusClient, collection_id: Optional[str] = None) -> List[str]:
    """Chunk collections that do not have the BM25 field yet."""
    if collection_id:
        names = [settings.PREFIX_COLLECTION_NAME + collection_id]
    else:
        names = client.list_collections()
    return [
        name for name in names
        if name.startswith(settings.PREFIX_COLLECTION_NAME)
        and not name.endswith(TMP_SUFFIX)
        and client.has_collection(name)
        and not has_sparse_field(client, name)
    ]

def count_rows(client: MilvusClient, collection_name: str) -> int:
    client.flush(collection_name)
    client.load_collection(collection_name)
    return client.query(collection_name, filter="", output_fields=["count(*)"])[0]["count(*)"]

def migrate_collection(client: MilvusClient, collection_name: str, batch_size: int = 500) -> int:
    """Copy one collection into the hybrid schema and swap it in. Returns the number of rows copied."""
    tmp_name = collection_name + TMP_SUFFIX
    if client.has_collection(tmp_name):
        # Leftover from an interrupted run
        client.drop_collection(tmp_name)

    schema, index_params = build_schema_and_index(client)
    client.create_collection(collection_name=tmp_name, schema=schema, index_params=index_params)

    old_count = count_rows(client, collection_name)
    copied = 0
    iterator = client.query_iterator(
        collection_name=collection_name,
        batch_size=batch_size,
        filter="",
        output_fields=["*"],
    )
    try:
        while True:
            batch = iterator.next()
            if not batch:
                break
            for row in batch:
                row.pop("pk", None)  # auto_id: the new collection assigns its own primary keys
            client.insert(collection_name=tmp_name, data=batch)
            copied += len(batch)
    except Exception:
        client.drop_collection(tmp_name)
        raise
    finally:
        iterator.close()

    new_count = count_rows(client, tmp_name)
    current_count = count_rows(client, collection_name)
    if not (old_count == copied == new_count == current_count):
        client.drop_collection(tmp_name)
        raise RuntimeError(
            f"Row count mismatch for {collection_name}: before={old_count}, copied={copied}, "
            f"new={new_count}, now={current_count}. Old collection kept unchanged."
        )

    client.drop_collection(collection_name)
    client.rename_collection(old_name=tmp_name, new_name=collection_name)
    return copied

def main():
    parser = argparse.ArgumentParser(description="Migrate Milvus chunk collections to hybrid (dense + BM25) search.")
    parser.add_argument("--dry-run", action="store_true", help="only list collections that need migration")
    parser.add_argument("--collection", help="collection id (without prefix) to migrate; default: all")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    client = MilvusClient(**get_milvus_connection_args())
    names = collections_to_migrate(client, args.collection)
    logger.info(f"{len(names)} collection(s) to migrate: {names}")
    if args.dry_run:
        return

    failed = []
    for name in names:
        try:
            copied = migrate_collection(client, name, args.batch_size)
            logger.info(f"Migrated {name}: {copied} rows")
        except Exception as e:
            logger.error(f"Failed to migrate {name}: {e}")
            failed.append(name)
    if failed:
        logger.error(f"{len(failed)} collection(s) not migrated: {failed}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
