"""Compare the baseline agent with the experimental strict question-anchor guard.

Uses the same LSA retriever, extractive answerer, sample PDF, evaluation set,
and top-k value. Only Config.strict_question_anchors changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paperqa.agent import PaperQAAgent
from paperqa.config import Config
from paperqa.evaluate import run


VARIANTS = ("baseline", "strict_question_anchors")


def compare_records(baseline: list[dict], guarded: list[dict]) -> dict[str, list[dict]]:
    base_by_id = {row["id"]: row for row in baseline}
    guard_by_id = {row["id"]: row for row in guarded}
    if set(base_by_id) != set(guard_by_id):
        raise ValueError("Baseline and guarded evaluations contain different question IDs.")

    newly_refused = []
    newly_answered = []
    reason_changes = []
    for question_id in sorted(base_by_id):
        before, after = base_by_id[question_id], guard_by_id[question_id]
        item = {
            "id": question_id,
            "question": before["question"],
            "answerable": before["answerable"],
            "type": before["type"],
            "baseline_found": before["found"],
            "guarded_found": after["found"],
            "baseline_reason": before["reason"],
            "guarded_reason": after["reason"],
        }
        if before["found"] and not after["found"]:
            newly_refused.append(item)
        elif not before["found"] and after["found"]:
            newly_answered.append(item)
        if before["reason"] != after["reason"]:
            reason_changes.append(item)

    return {
        "newly_refused": newly_refused,
        "newly_answered": newly_answered,
        "reason_changes": reason_changes,
    }


def render_report(comparison: dict[str, Any]) -> str:
    metrics = comparison["metrics"]
    lines = [
        "# Experimental question-anchor guard comparison",
        "",
        "The baseline and experimental runs use the same PDF, question set, LSA embedder, extractive answerer and top-k value. "
        "Only the opt-in strict question-anchor setting changes.",
        "",
        "## End-to-end results",
        "",
        "| Variant | Split | Answer accuracy | False abstain | Abstain recall on unanswerable | Wrong when answering | Citation hit | p50 ms | p95 ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in VARIANTS:
        for split in ("dev", "test", "all"):
            item = metrics[variant][split]
            lines.append(
                f"| {variant} | {split} | {item['answer_accuracy']:.1f}% | "
                f"{item['false_abstain_rate']:.1f}% | "
                f"{item['abstain_recall_on_unanswerable']:.1f}% | "
                f"{item['wrong_answer_rate_when_answering']:.1f}% | "
                f"{item['citation_hit_rate']:.1f}% | "
                f"{item['latency_ms_p50']:.2f} | {item['latency_ms_p95']:.2f} |"
            )

    changes = comparison["record_changes"]
    lines += [
        "",
        "## Behaviour changes",
        "",
        f"- Newly refused: **{len(changes['newly_refused'])}**",
        f"- Newly answered: **{len(changes['newly_answered'])}**",
        f"- Any refusal-reason change: **{len(changes['reason_changes'])}**",
        "",
        "### Newly refused questions",
        "",
        "| ID | Type | Answerable in evaluation? | Question | New refusal reason |",
        "|---|---|---:|---|---|",
    ]
    for item in changes["newly_refused"]:
        question = item["question"].replace("|", "\\|")
        lines.append(
            f"| {item['id']} | {item['type']} | {item['answerable']} | "
            f"{question} | {item['guarded_reason']} |"
        )
    lines += ["", "### Newly answered questions", "",
              "| ID | Type | Question |", "|---|---|---|"]
    for item in changes["newly_answered"]:
        question = item['question'].replace('|', '\\|')
        lines.append(f"| {item['id']} | {item['type']} | {question} |")

    lines += [
        "",
        "## Interpretation and limitations",
        "",
        "- This is a narrow lexical safeguard, not a semantic entailment model.",
        "- It checks all-caps technical acronyms in a question and requires recognised human-study evidence for explicit human-evaluation questions.",
        "- The rule may refuse an answer if a paper uses a full form without the acronym or describes a study using a synonym not yet included. It therefore remains opt-in.",
        "- The evaluation is one synthetic paper and 29 questions, not a real-world research-paper benchmark.",
        "- Compare answerable-question accuracy and false-abstain rate as well as abstention recall. A guard that refuses everything would have high refusal recall but would be useless.",
        "- Do not enable this by default or claim general entailment verification without broader, independent evaluation.",
        "",
    ]
    return "\n".join(lines)


def run_comparison(pdf: Path, eval_set: Path, output_dir: Path, top_k: int = 5) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    for variant, enabled in (("baseline", False), ("strict_question_anchors", True)):
        print(f"\n=== Running {variant} ===", flush=True)
        config = Config(embedder="lsa", llm="extractive", top_k=top_k,
                        strict_question_anchors=enabled)
        agent = PaperQAAgent.from_pdf(pdf, config)
        results[variant] = run(pdf, eval_set, output_dir / variant, agent)
        print(f"Saved {variant} evaluation.", flush=True)

    metrics = {
        variant: {
            split: results[variant]["end_to_end"][split]
            for split in ("dev", "test", "all")
        }
        for variant in VARIANTS
    }
    changes = compare_records(
        results["baseline"]["records"],
        results["strict_question_anchors"]["records"],
    )
    comparison = {
        "experiment": "strict_question_anchor_guard",
        "settings": {
            "pdf": str(pdf),
            "eval_set": str(eval_set),
            "embedder": "lsa",
            "answerer": "ExtractiveLLM",
            "top_k": top_k,
            "only_changed_setting": "strict_question_anchors: false -> true",
        },
        "metrics": metrics,
        "record_changes": changes,
        "warnings": [
            "This is a lexical anchor check, not a semantic entailment verifier.",
            "The rule is opt-in because acronym variants and unrecognised study terminology may cause false refusals.",
            "The test set is small and based on one synthetic paper.",
        ],
    }
    (output_dir / "anchor_guard_comparison.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "anchor_guard_comparison.md").write_text(
        render_report(comparison), encoding="utf-8"
    )
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=ROOT / "data" / "sample_paper.pdf")
    parser.add_argument("--eval-set", type=Path, default=ROOT / "eval" / "eval_set.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "anchor-guard")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    for path in (args.pdf, args.eval_set):
        if not path.is_file():
            parser.error(f"File not found: {path}")
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    try:
        result = run_comparison(args.pdf, args.eval_set, args.out, args.top_k)
    except (ImportError, OSError, ValueError) as exc:
        print(f"Anchor-guard comparison failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "output_dir": str(args.out),
        "test_metrics": result["metrics"]["strict_question_anchors"]["test"],
        "newly_refused": [x["id"] for x in result["record_changes"]["newly_refused"]],
        "newly_answered": [x["id"] for x in result["record_changes"]["newly_answered"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
