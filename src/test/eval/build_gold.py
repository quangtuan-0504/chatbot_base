"""Find the gold chunks of each question by matching its evidence sentence against the indexed chunks.

Coverage of a chunk = share of evidence characters inside contiguous matches of >= 20 characters
(difflib.SequenceMatcher) after normalization and removing all whitespace. Gold = chunks with coverage >= max(0.5, best - 0.1);
if the best chunk covers < 0.9 (evidence split across chunks), add neighbours covering >= 0.2.
Questions with > 3 gold chunks or best coverage < 0.9 are flagged for manual review.

Run: venv/bin/python src/test/eval/build_gold.py
"""
import difflib
import json
import os

from eval_common import COLLECTION_ID, GOLD_PATH, RESULTS_DIR, load_questions, normalize

from pymilvus import MilvusClient
from pymongo import MongoClient
from src.configs import settings
from src.helpers.milvus.milvus import get_milvus_connection_args

MIN_BLOCK = 20


def squeeze(text):
    """Normalize and drop all whitespace: Marker glues words together on some PDFs (51-bgtvt-kem)."""
    return normalize(text).replace(" ", "")


def coverage(evidence, chunk):
    matcher = difflib.SequenceMatcher(None, evidence, chunk, autojunk=False)
    return sum(b.size for b in matcher.get_matching_blocks() if b.size >= MIN_BLOCK) / len(evidence)


def main():
    db = MongoClient(settings.MONGO_URL)[settings.MONGO_DB]
    milvus = MilvusClient(**get_milvus_connection_args())
    collection_name = settings.PREFIX_COLLECTION_NAME + COLLECTION_ID
    file_ids = {d["file_name"]: str(d["_id"]) for d in db.documents.find({"collection_id": COLLECTION_ID})}

    chunks_by_file = {}
    gold = {}
    for q in load_questions():
        file_id = file_ids[q["file"]]
        if file_id not in chunks_by_file:
            rows = milvus.query(collection_name=collection_name, filter="file_id == {fid}",
                                filter_params={"fid": file_id}, output_fields=["text", "chunk_index_in_file"], limit=16000)
            chunks_by_file[file_id] = {r["chunk_index_in_file"]: squeeze(r["text"]) for r in rows}
        chunks = chunks_by_file[file_id]
        if not chunks:
            raise RuntimeError(f"{q['file']} has no chunks in Milvus; index it before building gold")

        evidence = squeeze(q["cau_bang_chung"])
        cov = {i: coverage(evidence, text) for i, text in chunks.items()}
        best_index = max(cov, key=cov.get)
        best = cov[best_index]
        gold_indices = {i for i, v in cov.items() if v >= max(0.5, best - 0.1)}
        if best < 0.9:
            gold_indices |= {j for j in (best_index - 1, best_index + 1) if cov.get(j, 0) >= 0.2}

        top = sorted(cov.items(), key=lambda kv: kv[1], reverse=True)[:8]
        gold[q["id"]] = {
            "file": q["file"],
            "file_id": file_id,
            "gold": sorted(gold_indices),
            "best_coverage": round(best, 3),
            "flag": len(gold_indices) > 3 or best < 0.9,
            "top_coverage": [[i, round(v, 3)] for i, v in top],
        }

    # Manual fixes after review (see the file's _note); they replace the automatic gold of those questions
    overrides_path = os.path.join(RESULTS_DIR, "manual_gold_overrides.json")
    if os.path.exists(overrides_path):
        with open(overrides_path, encoding="utf-8") as f:
            overrides = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
        for qid, fix in overrides.items():
            gold[qid].update({"gold": fix["gold"], "manual": fix["reason"], "flag": False})

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(GOLD_PATH, "w", encoding="utf-8") as f:
        json.dump(gold, f, ensure_ascii=False, indent=1)
    flagged = [k for k, v in gold.items() if v["flag"]]
    sizes = [len(v["gold"]) for v in gold.values()]
    print(f"{len(gold)} questions, gold sizes min/max {min(sizes)}/{max(sizes)}, flagged {len(flagged)}: {flagged}")


if __name__ == "__main__":
    main()
