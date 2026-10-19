"""Shared paths and helpers for the retrieval / answer evaluation (report section 11.1)."""
import json
import os
import re
import sys
import unicodedata

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO_ROOT)

DATASET_DIR = os.getenv(
    "EVAL_DATASET_DIR",
    os.path.join(os.path.dirname(REPO_ROOT), "traffic_law_dataset_eval"),
)
QUESTIONS_PATH = os.path.join(DATASET_DIR, "questions_answers_labels", "eval_giao_thong.jsonl")
RESULTS_DIR = os.getenv("EVAL_RESULTS_DIR", os.path.join(DATASET_DIR, "results"))
GOLD_PATH = os.path.join(RESULTS_DIR, "gold_chunks.json")
RUNS_PATH = os.path.join(RESULTS_DIR, "runs.jsonl")
JUDGE_PATH = os.path.join(RESULTS_DIR, "judgments.jsonl")

COLLECTION_ID = os.getenv("EVAL_COLLECTION_ID", "6ad5d6d3b3ca9b3aa245313a")
CHAT_MODEL = os.getenv("EVAL_CHAT_MODEL", "gpt-6-luna")

# A: full system, B: ablation 1 (dense only), C: ablation 2 (no query rewrite)
CONFIGS = {
    "A": {"hybrid": True, "rewrite_turns": 3},
    "B": {"hybrid": False, "rewrite_turns": 3},
    "C": {"hybrid": True, "rewrite_turns": 0},
}


def load_questions():
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def is_single(q):
    return q["ma_hoi_thoai"] is None


def is_follow_up(q):
    return q["ma_hoi_thoai"] is not None and q["thu_tu_luot"] > 1


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize(text):
    """NFC, lowercase, drop Markdown symbols Marker adds, collapse whitespace."""
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[*_#|`>\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
