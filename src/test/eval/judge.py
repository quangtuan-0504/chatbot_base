"""LLM-as-judge for the evaluation runs: correctness, faithfulness, context recall, and rewrite quality.

The judge never sees the configuration name, and items are judged in shuffled order.
Results are cached in judgments.jsonl by (id, config, metric), so re-running only judges what is missing.

Run: venv/bin/python src/test/eval/judge.py [--workers 8]
"""
import argparse
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor

from eval_common import CHAT_MODEL, JUDGE_PATH, RUNS_PATH, append_jsonl, is_follow_up, load_questions, read_jsonl

from openai import OpenAI
from src.configs import settings

JUDGE_MODEL = CHAT_MODEL

CORRECTNESS_PROMPT = """Bạn là giám khảo chấm câu trả lời về luật giao thông Việt Nam.
So sánh CÂU TRẢ LỜI CỦA HỆ THỐNG với CÂU TRẢ LỜI CHUẨN cho câu hỏi dưới đây.
- 1: đúng và đủ các ý chính của câu trả lời chuẩn (mức phạt, điều khoản, điều kiện...), không có thông tin sai mâu thuẫn.
- 0.5: đúng một phần: thiếu ý chính, hoặc đúng ý chính nhưng kèm chi tiết sai không quan trọng.
- 0: sai, mâu thuẫn với câu trả lời chuẩn, hoặc không trả lời.
Cách diễn đạt khác nhau không bị trừ điểm. Thông tin thêm đúng không bị trừ điểm.
Thiếu số hiệu điều/khoản không bị trừ điểm nếu nội dung quy định đúng, trừ khi câu hỏi hỏi chính số hiệu đó.

CÂU HỎI: {question}
CÂU TRẢ LỜI CHUẨN: {gold}
CÂU TRẢ LỜI CỦA HỆ THỐNG: {answer}

Trả về JSON: {{"score": 1 | 0.5 | 0, "reason": "<một câu>"}}"""

FAITHFULNESS_PROMPT = """Tách CÂU TRẢ LỜI thành các ý khẳng định độc lập về nội dung quy định.
Bỏ qua câu chào, câu dẫn dắt, dòng "Nguồn:", và câu nói rằng tài liệu không có thông tin (đó là từ chối, không phải khẳng định).
Nếu không còn ý nào, trả về danh sách rỗng.
Với mỗi ý, xét xem NGỮ CẢNH có hỗ trợ ý đó không (supported = true chỉ khi suy ra được trực tiếp từ ngữ cảnh).

NGỮ CẢNH:
{context}

CÂU TRẢ LỜI:
{answer}

Trả về JSON: {{"claims": [{{"claim": "<ý>", "supported": true | false}}]}}"""

CONTEXT_RECALL_PROMPT = """Tách CÂU TRẢ LỜI CHUẨN thành các ý độc lập.
Với mỗi ý, xét xem NGỮ CẢNH có chứa thông tin đó không (covered = true chỉ khi ngữ cảnh nêu rõ thông tin này).

NGỮ CẢNH:
{context}

CÂU TRẢ LỜI CHUẨN:
{gold}

Trả về JSON: {{"statements": [{{"statement": "<ý>", "covered": true | false}}]}}"""

REWRITE_PROMPT = """Một hệ thống hỏi đáp viết lại câu hỏi nối tiếp trong hội thoại thành câu hỏi độc lập để tìm kiếm tài liệu.

LỊCH SỬ HỘI THOẠI:
{history}

CÂU HỎI NỐI TIẾP: {question}
CÂU ĐÃ VIẾT LẠI: {rewritten}

Đánh giá:
- standalone: câu viết lại có hiểu được đầy đủ mà không cần lịch sử không.
- preserves_meaning: câu viết lại có giữ đúng ý định của câu hỏi nối tiếp không (không thêm, bớt hay đổi chủ thể).
Trả về JSON: {{"standalone": true | false, "preserves_meaning": true | false, "reason": "<một câu>"}}"""

client = OpenAI(api_key=settings.openai_api_key)
write_lock = threading.Lock()


def ask(prompt):
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def ratio(items, key):
    return sum(bool(i.get(key)) for i in items) / len(items) if items else None


def judge(task):
    run, question, metric, history_text = task
    if metric == "correctness":
        out = ask(CORRECTNESS_PROMPT.format(question=question["cau_hoi"], gold=question["cau_tra_loi"], answer=run["answer"]))
        value = float(out["score"])
    elif metric == "faithfulness":
        out = ask(FAITHFULNESS_PROMPT.format(context=run["context"] or "(trống)", answer=run["answer"]))
        value = ratio(out.get("claims", []), "supported")
    elif metric == "context_recall":
        out = ask(CONTEXT_RECALL_PROMPT.format(context=run["context"] or "(trống)", gold=question["cau_tra_loi"]))
        value = ratio(out.get("statements", []), "covered")
    else:  # rewrite
        out = ask(REWRITE_PROMPT.format(history=history_text, question=question["cau_hoi"], rewritten=run["search_query"]))
        value = float(bool(out.get("standalone")) and bool(out.get("preserves_meaning")))
    row = {"id": run["id"], "config": run["config"], "metric": metric, "value": value, "detail": out}
    with write_lock:
        append_jsonl(JUDGE_PATH, row)
    return row


def history_text(question, by_id):
    lines = []
    for turn in range(1, question["thu_tu_luot"]):
        prev = by_id[f"{question['ma_hoi_thoai']}-{turn}"]
        lines += [f"user: {prev['cau_hoi']}", f"assistant: {prev['cau_tra_loi']}"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    by_id = {q["id"]: q for q in load_questions()}
    runs = {}
    for r in read_jsonl(RUNS_PATH):
        if not r.get("error"):
            runs[(r["id"], r["config"])] = r  # keep the latest successful run
    done = {(j["id"], j["config"], j["metric"]) for j in read_jsonl(JUDGE_PATH)}

    tasks = []
    for (qid, config), run in runs.items():
        question = by_id[qid]
        metrics = ["correctness", "faithfulness", "context_recall"]
        if config == "A" and is_follow_up(question):
            metrics.append("rewrite")
        for metric in metrics:
            if (qid, config, metric) not in done:
                tasks.append((run, question, metric, history_text(question, by_id) if metric == "rewrite" else ""))
    random.Random(0).shuffle(tasks)
    print(f"{len(tasks)} judgments to do")

    failed = 0
    with ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(judge, t) for t in tasks]
        for n, f in enumerate(futures, start=1):
            try:
                f.result()
            except Exception as e:
                failed += 1
                print(f"judge failed: {e}", flush=True)
            if n % 50 == 0:
                print(f"{n}/{len(tasks)}", flush=True)
    print(f"done, {failed} failed (re-run to retry them)")


if __name__ == "__main__":
    main()
