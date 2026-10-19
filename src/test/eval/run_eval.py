"""Answer the evaluation questions with configurations A, B, C and log ranking, context and answer.

A and B answer the 90 single-turn questions; A and C answer the 30 conversation turns.
Configurations are interleaved per question so latency drift affects them equally.
Conversation history is fixed to the gold question/answer of earlier turns, so A and C see the same history.
Already answered (id, config) pairs in runs.jsonl are skipped, so the script can be resumed.

Run: venv/bin/python src/test/eval/run_eval.py [--limit N] [--configs A,B,C]
"""
import argparse
import time

from eval_common import (CHAT_MODEL, COLLECTION_ID, CONFIGS, RUNS_PATH, append_jsonl, is_single,
                         load_questions, read_jsonl)

from src.configs import settings
from src.loggers.logapp import logger
from src.tools.load_resources import load_resource

MAX_RETRIES = 3


def gold_history(question, questions_by_id):
    """Earlier turns of the same conversation, with gold answers, in the router's message format."""
    history = []
    for turn in range(1, question["thu_tu_luot"]):
        prev = questions_by_id[f"{question['ma_hoi_thoai']}-{turn}"]
        history.append({"role": "user", "content": [{"type": "text", "text": prev["cau_hoi"]}]})
        history.append({"role": "assistant", "content": [{"type": "text", "text": prev["cau_tra_loi"]}]})
    return history


def answer(chatbot, question, history, config):
    settings.RAG_HYBRID_ENABLED = CONFIGS[config]["hybrid"]
    settings.RAG_REWRITE_HISTORY_TURNS = CONFIGS[config]["rewrite_turns"]
    debug = {}
    text, sources = "", []
    start = time.perf_counter()
    stream = chatbot.chat_stream(
        query=question["cau_hoi"], model_name=CHAT_MODEL, image_urls=[], history_chat=history,
        collection_name=COLLECTION_ID, debug=debug,
    )
    for chunk in stream:
        if isinstance(chunk, str):
            text += chunk
        elif isinstance(chunk, list):
            sources = chunk
            break  # images come next; not needed for the evaluation
    stream.close()
    return {
        "id": question["id"],
        "config": config,
        "question": question["cau_hoi"],
        "search_query": debug.get("search_query"),
        "hybrid": debug.get("hybrid"),
        "ranking": debug.get("ranking", [])[:10],
        "context": debug.get("context", ""),
        "sources": sources,
        "answer": text,
        "search_metrics": debug.get("search_metrics"),
        "total_answer_ms": round((time.perf_counter() - start) * 1000, 1),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="only the first N questions of each set (dry run)")
    parser.add_argument("--configs", default="A,B,C")
    args = parser.parse_args()
    wanted = set(args.configs.split(","))

    questions = load_questions()
    by_id = {q["id"]: q for q in questions}
    single = [q for q in questions if is_single(q)][: args.limit]
    conversation = [q for q in questions if not is_single(q)][: args.limit]
    jobs = [(q, c) for q in single for c in ("A", "B") if c in wanted]
    jobs += [(q, c) for q in conversation for c in ("A", "C") if c in wanted]

    done = {(r["id"], r["config"]) for r in read_jsonl(RUNS_PATH) if not r.get("error")}
    jobs = [(q, c) for q, c in jobs if (q["id"], c) not in done]
    print(f"{len(jobs)} runs to do ({len(done)} already done)")

    chatbot = load_resource()[CHAT_MODEL]
    for n, (question, config) in enumerate(jobs, start=1):
        history = gold_history(question, by_id) if not is_single(question) else []
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                row = answer(chatbot, question, history, config)
                break
            except Exception as e:
                logger.warning(f"{question['id']} {config} attempt {attempt} failed: {e}")
                row = {"id": question["id"], "config": config, "error": f"{type(e).__name__}: {e}"}
                time.sleep(5 * attempt)
        append_jsonl(RUNS_PATH, row)
        status = f"ERROR {row['error']}" if row.get("error") else f"{len(row['answer'])} chars"
        print(f"[{n}/{len(jobs)}] {question['id']} {config} {status}", flush=True)


if __name__ == "__main__":
    main()
