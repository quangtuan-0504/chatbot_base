"""Aggregate runs + gold + judgments into the tables of report section 11.1.

Retrieval: Hit@3, Hit@10, MRR (ranking cut at 10), File Hit@3, from gold_chunks.json.
Answer: correctness, faithfulness, context recall from judgments.jsonl.
Paired tests: exact McNemar for Hit@k, paired bootstrap (10,000 resamples) 95% CI of the mean difference.

Run: venv/bin/python src/test/eval/score.py   -> results/summary.json, results/summary.md
"""
import json
import math
import os

import numpy as np
from eval_common import GOLD_PATH, JUDGE_PATH, RESULTS_DIR, RUNS_PATH, is_follow_up, is_single, load_questions, read_jsonl

GROUPS = {"ngu_nghia": "Ngữ nghĩa", "tu_khoa": "Từ khóa chính xác"}


def first_gold_rank(run, gold):
    keys = {(gold["file_id"], i) for i in gold["gold"]}
    for hit in run["ranking"][:10]:
        if (hit["file_id"], hit["chunk_index_in_file"]) in keys:
            return hit["rank"]
    return None


def retrieval_metrics(run, gold):
    rank = first_gold_rank(run, gold)
    top3_files = {h["file_id"] for h in run["ranking"][:3]}
    return {
        "hit3": float(rank is not None and rank <= 3),
        "hit10": float(rank is not None),
        "mrr": 1 / rank if rank else 0.0,
        "file_hit3": float(gold["file_id"] in top3_files),
    }


def mcnemar_exact(a, b):
    """Two-sided exact McNemar p-value for paired binary outcomes."""
    only_a = sum(1 for x, y in zip(a, b) if x and not y)
    only_b = sum(1 for x, y in zip(a, b) if y and not x)
    n = only_a + only_b
    if n == 0:
        return 1.0, only_a, only_b
    tail = sum(math.comb(n, i) for i in range(min(only_a, only_b) + 1)) / 2 ** n
    return min(1.0, 2 * tail), only_a, only_b


def bootstrap_ci(a, b, n_resamples=10_000, seed=0):
    """95% CI of mean(a - b) over paired items, ignoring pairs where either side is missing."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return None
    diff = np.array([x - y for x, y in pairs])
    rng = np.random.default_rng(seed)
    means = diff[rng.integers(0, len(diff), (n_resamples, len(diff)))].mean(axis=1)
    return {"mean_diff": float(diff.mean()), "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))], "n": len(diff)}


def mean(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def summarize(ids, config, rows):
    """Mean of every metric over the given question ids for one configuration."""
    items = [rows[(i, config)] for i in ids]
    metrics = ["hit3", "hit10", "mrr", "file_hit3", "context_recall", "correctness", "faithfulness"]
    out = {m: mean([it.get(m) for it in items]) for m in metrics}
    total_ms = [it["search_metrics"]["total_ms"] for it in items if it.get("search_metrics")]
    out["search_ms_mean"] = mean(total_ms)
    out["search_ms_p95"] = float(np.percentile(total_ms, 95)) if total_ms else None
    out["n"] = len(items)
    return out


def compare(ids, a, b, rows):
    """Paired comparison of configuration a against b on the same question ids."""
    result = {}
    for m in ("hit3", "hit10"):
        p, only_a, only_b = mcnemar_exact([rows[(i, a)][m] for i in ids], [rows[(i, b)][m] for i in ids])
        result[m] = {"p_mcnemar": p, f"only_{a}": only_a, f"only_{b}": only_b}
    for m in ("hit3", "mrr", "context_recall", "correctness", "faithfulness"):
        result.setdefault(m, {})["bootstrap"] = bootstrap_ci([rows[(i, a)].get(m) for i in ids], [rows[(i, b)].get(m) for i in ids])
    return result


def fmt(v, pct=False):
    if v is None:
        return ""
    return f"{v * 100:.1f}%" if pct else f"{v:.3f}"


def main():
    questions = load_questions()
    by_id = {q["id"]: q for q in questions}
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold = json.load(f)

    rows = {}
    for r in read_jsonl(RUNS_PATH):
        if not r.get("error"):
            rows[(r["id"], r["config"])] = {**r, **retrieval_metrics(r, gold[r["id"]])}
    for j in read_jsonl(JUDGE_PATH):
        if (j["id"], j["config"]) in rows:
            rows[(j["id"], j["config"])][j["metric"]] = j["value"]

    single = [q["id"] for q in questions if is_single(q) and (q["id"], "A") in rows and (q["id"], "B") in rows]
    follow = [q["id"] for q in questions if is_follow_up(q) and (q["id"], "A") in rows and (q["id"], "C") in rows]
    first_turns = [q["id"] for q in questions if q["ma_hoi_thoai"] and q["thu_tu_luot"] == 1
                   and (q["id"], "A") in rows and (q["id"], "C") in rows]

    rewrite_tokens = [rows[(i, "A")]["search_metrics"]["rewrite_prompt_tokens"] + rows[(i, "A")]["search_metrics"]["rewrite_completion_tokens"] for i in follow]
    rewrite_ms = [rows[(i, "A")]["search_metrics"]["rewrite_ms"] for i in follow]

    summary = {
        "n_single": len(single),
        "n_follow_up": len(follow),
        "rq1": {c: summarize(single, c, rows) for c in ("A", "B")},
        "rq1_by_group": {g: {c: summarize([i for i in single if by_id[i]["nhom"] == g], c, rows) for c in ("A", "B")} for g in GROUPS},
        "rq1_test": compare(single, "A", "B", rows),
        "rq1_test_by_group": {g: compare([i for i in single if by_id[i]["nhom"] == g], "A", "B", rows) for g in GROUPS},
        "rq2": {c: summarize(follow, c, rows) for c in ("A", "C")},
        "rq2_test": compare(follow, "A", "C", rows),
        "rq2_rewrite": {
            "tokens_mean": mean(rewrite_tokens),
            "ms_mean": mean(rewrite_ms),
            "quality_ok": mean([rows[(i, "A")].get("rewrite") for i in follow]),
        },
        "first_turn_same_query": mean([float(rows[(i, "A")]["search_query"] == rows[(i, "C")]["search_query"]) for i in first_turns]),
        "empty_answers": {c: sum(1 for (i, cc), r in rows.items() if cc == c and not r["answer"].strip()) for c in ("A", "B", "C")},
    }

    wrong = {}
    for c, ids in (("A", single + follow), ("B", single), ("C", follow)):
        wrong[c] = [
            {"id": i, "question": by_id[i]["cau_hoi"], "correctness": rows[(i, c)].get("correctness"),
             "hit3": rows[(i, c)]["hit3"], "search_query": rows[(i, c)]["search_query"], "answer": rows[(i, c)]["answer"][:400],
             "gold_answer": by_id[i]["cau_tra_loi"][:400]}
            for i in ids if rows[(i, c)].get("correctness") is not None and rows[(i, c)]["correctness"] < 1
        ]
    summary["wrong_counts"] = {c: len(v) for c, v in wrong.items()}

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(RESULTS_DIR, "wrong_answers.json"), "w", encoding="utf-8") as f:
        json.dump(wrong, f, ensure_ascii=False, indent=1)

    lines = [f"RQ1 ({len(single)} single-turn questions)", "| Config | Hit@3 | Hit@10 | MRR | File Hit@3 | Context recall | Correctness | Faithfulness | Search ms mean / p95 |", "|---|---|---|---|---|---|---|---|---|"]
    for c, s in summary["rq1"].items():
        lines.append(f"| {c} | {fmt(s['hit3'], 1)} | {fmt(s['hit10'], 1)} | {fmt(s['mrr'])} | {fmt(s['file_hit3'], 1)} | {fmt(s['context_recall'])} | {fmt(s['correctness'])} | {fmt(s['faithfulness'])} | {s['search_ms_mean']:.0f} / {s['search_ms_p95']:.0f} |")
    lines += ["", "Hit@3 by group", "| Config | " + " | ".join(GROUPS.values()) + " |", "|---|---|---|"]
    for c in ("A", "B"):
        lines.append(f"| {c} | " + " | ".join(fmt(summary["rq1_by_group"][g][c]["hit3"], 1) for g in GROUPS) + " |")
    lines += ["", f"RQ2 ({len(follow)} follow-up turns)", "| Config | Hit@3 | MRR | Context recall | Correctness |", "|---|---|---|---|---|"]
    for c, s in summary["rq2"].items():
        lines.append(f"| {c} | {fmt(s['hit3'], 1)} | {fmt(s['mrr'])} | {fmt(s['context_recall'])} | {fmt(s['correctness'])} |")
    lines += ["", "```", json.dumps({k: summary[k] for k in ("rq1_test", "rq1_test_by_group", "rq2_test", "rq2_rewrite", "first_turn_same_query", "empty_answers", "wrong_counts")}, ensure_ascii=False, indent=1), "```"]
    with open(os.path.join(RESULTS_DIR, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
