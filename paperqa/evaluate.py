"""Evaluation harness: retrieval quality, answer accuracy, abstention behaviour, citation quality, latency.

An item is {id, question, answerable, evidence[], must_include[[alt,...],...], split, type}.
* A chunk is *relevant* if it contains any `evidence` string (whitespace/case-insensitive).
* An answer is *correct* if every group in `must_include` has at least one alternative in the answer text.
* An unanswerable question is handled correctly only if the agent abstains.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from .agent import PaperQAAgent
from .text import squash


def load_eval(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text())["items"]


def is_relevant(chunk_text: str, evidence: list[str]) -> bool:
    flat = squash(chunk_text)
    return any(squash(e) in flat for e in evidence)


def answer_correct(answer_text: str, must_include: list[list[str]]) -> bool:
    flat = squash(answer_text)
    return all(any(squash(alt) in flat for alt in group) for group in must_include)


def _pct(x: float) -> float:
    return round(100 * x, 1)


# ----------------------------------------------------------------------------- retrieval
def eval_retrieval(agent: PaperQAAgent, items: list[dict], mode: str, ks=(1, 3, 5)) -> dict:
    ans = [i for i in items if i["answerable"]]
    hits_at = {k: 0 for k in ks}
    rr = []
    for it in ans:
        results = agent.index.search(it["question"], k=max(ks), mode=mode)
        first = next((h.rank for h in results if is_relevant(h.chunk.text, it["evidence"])), None)
        rr.append(1 / first if first else 0.0)
        for k in ks:
            hits_at[k] += bool(first and first <= k)
    n = len(ans) or 1
    return {"n": len(ans), **{f"hit@{k}": _pct(v / n) for k, v in hits_at.items()}, "mrr": round(sum(rr) / n, 3)}


# ----------------------------------------------------------------------------- end to end
def eval_end_to_end(agent: PaperQAAgent, items: list[dict]) -> tuple[dict, list[dict]]:
    records = []
    for it in items:
        a = agent.ask(it["question"])
        rec = {"id": it["id"], "split": it["split"], "type": it["type"], "answerable": it["answerable"],
               "question": it["question"], "found": a.found, "reason": a.reason, "answer": a.text,
               "latency_ms": round(a.latency_ms, 2), "cited_sections": [c.section for c in a.citations]}
        if it["answerable"]:
            rec["correct"] = a.found and answer_correct(a.text, it["must_include"])
            rec["citation_ok"] = a.found and any(
                is_relevant(agent.chunks[c.chunk_id].text, it["evidence"]) for c in a.citations)
        else:
            rec["correct"] = not a.found
        records.append(rec)
    return summarize(records), records


def summarize(records: list[dict], split: str | None = None) -> dict:
    rs = [r for r in records if split is None or r["split"] == split]
    ans = [r for r in rs if r["answerable"]]
    una = [r for r in rs if not r["answerable"]]
    answered = [r for r in ans if r["found"]]
    lat = sorted(r["latency_ms"] for r in rs) or [0.0]
    out = {
        "split": split or "all",
        "n_answerable": len(ans),
        "n_unanswerable": len(una),
        "answer_accuracy": _pct(sum(r["correct"] for r in ans) / (len(ans) or 1)),
        "false_abstain_rate": _pct(sum(not r["found"] for r in ans) / (len(ans) or 1)),
        "abstain_recall_on_unanswerable": _pct(sum(r["correct"] for r in una) / (len(una) or 1)),
        "wrong_answer_rate_when_answering": _pct(
            sum(not r["correct"] for r in answered) / (len(answered) or 1)),
        "citation_hit_rate": _pct(sum(r["citation_ok"] for r in answered) / (len(answered) or 1)),
        "overall_accuracy": _pct(sum(r["correct"] for r in rs) / (len(rs) or 1)),
        "latency_ms_p50": round(statistics.median(lat), 2),
        "latency_ms_p95": round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 2),
    }
    return out


def by_type(records: list[dict]) -> dict[str, dict]:
    types = sorted({r["type"] for r in records})
    return {t: {"n": sum(r["type"] == t for r in records),
                "accuracy": _pct(sum(r["correct"] for r in records if r["type"] == t)
                                 / sum(r["type"] == t for r in records))} for t in types}


# ----------------------------------------------------------------------------- report
def run(pdf: str | Path, eval_path: str | Path, out_dir: str | Path, agent: PaperQAAgent | None = None) -> dict:
    agent = agent or PaperQAAgent.from_pdf(pdf)
    items = load_eval(eval_path)
    backend = {"embedder": agent.config.embedder, "llm": type(agent.llm).__name__, "top_k": agent.config.top_k,
               "chunks": len(agent.chunks)}
    retrieval = {m: eval_retrieval(agent, items, m) for m in ("bm25", "dense", "hybrid")}
    e2e, records = eval_end_to_end(agent, items)
    result = {"backend": backend, "retrieval": retrieval, "end_to_end": {
        "all": e2e, "dev": summarize(records, "dev"), "test": summarize(records, "test")},
        "by_type": by_type(records), "records": records}

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "eval_results.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    (out / "eval_report.md").write_text(render_markdown(result))
    return result


def render_markdown(r: dict) -> str:
    b = r["backend"]
    lines = [f"# Evaluation report", "",
             f"Backend: embedder=`{b['embedder']}`, answerer=`{b['llm']}`, top_k={b['top_k']}, chunks={b['chunks']}", "",
             "## Retrieval (answerable questions)", "", "| mode | hit@1 | hit@3 | hit@5 | MRR |", "|---|---|---|---|---|"]
    for m, v in r["retrieval"].items():
        lines.append(f"| {m} | {v['hit@1']}% | {v['hit@3']}% | {v['hit@5']}% | {v['mrr']} |")
    lines += ["", "## End-to-end", "",
              "| split | answerable | unanswerable | answer accuracy | false-abstain | abstain recall | wrong when answering | citation hit | p50 ms | p95 ms |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for s in ("dev", "test", "all"):
        v = r["end_to_end"][s]
        lines.append(f"| {s} | {v['n_answerable']} | {v['n_unanswerable']} | {v['answer_accuracy']}% | {v['false_abstain_rate']}% | "
                     f"{v['abstain_recall_on_unanswerable']}% | {v['wrong_answer_rate_when_answering']}% | {v['citation_hit_rate']}% | "
                     f"{v['latency_ms_p50']} | {v['latency_ms_p95']} |")
    lines += ["", "## Accuracy by question type", "", "| type | n | accuracy |", "|---|---|---|"]
    for t, v in r["by_type"].items():
        lines.append(f"| {t} | {v['n']} | {v['accuracy']}% |")
    lines += ["", "## Failures", ""]
    for rec in r["records"]:
        if not rec["correct"]:
            lines.append(f"- **{rec['id']}** ({rec['split']}, {rec['type']}): {rec['question']}  \n"
                         f"  found={rec['found']} reason={rec['reason']} answer: {rec['answer'][:160]}")
    return "\n".join(lines) + "\n"
