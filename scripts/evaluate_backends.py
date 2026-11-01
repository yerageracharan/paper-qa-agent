"""Compare the offline LSA and Sentence Transformers embedders on the same paper/eval set.

The default answerer is extractive, so this experiment requires no paid LLM API key.
Only the embedding backend changes between the two runs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paperqa.agent import PaperQAAgent
from paperqa.config import Config
from paperqa.evaluate import run


EMBEDDERS = ("lsa", "st")
RETRIEVAL_MODES = ("bm25", "dense", "hybrid")
SPLITS = ("dev", "test", "all")


def render_comparison(results: dict[str, dict[str, Any]]) -> str:
    missing = set(EMBEDDERS) - set(results)
    if missing:
        raise ValueError(f"Missing backend results: {sorted(missing)}")

    answerers = {result.get("backend", {}).get("llm") for result in results.values()}
    if len(answerers) != 1:
        raise ValueError("Both embedder runs must use the same answerer to isolate retrieval effects.")

    answerer = next(iter(answerers))
    lines = [
        "# Paper Q&A backend comparison",
        "",
        f"Answerer held constant: {answerer}.",
        "The only intended difference between runs is the embedding backend (LSA versus Sentence Transformers).",
        "Both runs use the same PDF, evaluation questions, top-k setting, and evaluation code.",
        "",
        "## Retrieval quality",
        "",
        "| Embedder | Mode | Hit@1 | Hit@3 | Hit@5 | MRR |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for embedder in EMBEDDERS:
        retrieval = results[embedder]["retrieval"]
        for mode in RETRIEVAL_MODES:
            metric = retrieval[mode]
            lines.append(
                f"| {embedder} | {mode} | {metric['hit@1']:.1f}% | "
                f"{metric['hit@3']:.1f}% | {metric['hit@5']:.1f}% | {metric['mrr']:.3f} |"
            )

    lines += [
        "",
        "## End-to-end answer and refusal behaviour",
        "",
        "| Embedder | Split | Answer accuracy | False abstain | Abstain recall on unanswerable | Wrong when answering | Citation hit | p50 ms | p95 ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for embedder in EMBEDDERS:
        for split in SPLITS:
            metric = results[embedder]["end_to_end"][split]
            lines.append(
                f"| {embedder} | {split} | {metric['answer_accuracy']:.1f}% | "
                f"{metric['false_abstain_rate']:.1f}% | "
                f"{metric['abstain_recall_on_unanswerable']:.1f}% | "
                f"{metric['wrong_answer_rate_when_answering']:.1f}% | "
                f"{metric['citation_hit_rate']:.1f}% | "
                f"{metric['latency_ms_p50']:.2f} | {metric['latency_ms_p95']:.2f} |"
            )

    lines += ["", "## Backend details", "", "| Embedder | Answerer | Top-k | Chunks |", "|---|---|---:|---:|"]
    for embedder in EMBEDDERS:
        backend = results[embedder]["backend"]
        lines.append(
            f"| {backend['embedder']} | {backend['llm']} | {backend['top_k']} | {backend['chunks']} |"
        )

    lines += [
        "",
        "## Interpretation rules",
        "",
        "- This is a controlled comparison on one synthetic three-page paper and 29 questions; it is not a real-paper benchmark.",
        "- A better retrieval score does not automatically mean better answers. Read answer accuracy, refusals, citation hits, and latency together.",
        "- The test split is reported as a fixed comparison, not used to tune thresholds or settings.",
        "- The offline answerer is kept constant. This experiment does not measure Claude/Anthropic.",
        "- The st run downloads the public Sentence Transformers model on first use; no API key is required, but internet access is.",
        "- The answerer and embedder are not interchangeable: the embedder finds passages; the answerer writes or extracts the response.",
        "",
    ]
    return "\n".join(lines)


def run_comparison(
    pdf: Path,
    eval_set: Path,
    output_dir: Path,
    answerer: str = "extractive",
    top_k: int = 5,
) -> dict[str, dict[str, Any]]:
    if answerer == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY is not set. Use --llm extractive for the no-key experiment.")

    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}

    for embedder in EMBEDDERS:
        print(f"\n=== Evaluating embedder: {embedder} (answerer: {answerer}) ===", flush=True)
        config = Config(embedder=embedder, llm=answerer, top_k=top_k)
        agent = PaperQAAgent.from_pdf(pdf, config)
        run_dir = output_dir / embedder
        results[embedder] = run(pdf, eval_set, run_dir, agent)
        print(f"Saved {embedder} results to {run_dir}", flush=True)

    (output_dir / "backend_comparison.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "backend_comparison.md").write_text(
        render_comparison(results), encoding="utf-8"
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=ROOT / "data" / "sample_paper.pdf")
    parser.add_argument("--eval-set", type=Path, default=ROOT / "eval" / "eval_set.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "backend-comparison")
    parser.add_argument("--llm", choices=("extractive", "anthropic"), default="extractive")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    for path in (args.pdf, args.eval_set):
        if not path.is_file():
            parser.error(f"File not found: {path}")
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")

    try:
        results = run_comparison(args.pdf, args.eval_set, args.out, args.llm, args.top_k)
    except (ImportError, OSError, ValueError) as exc:
        print(f"Backend comparison failed: {exc}", file=sys.stderr)
        return 1

    print("\n=== Comparison finished ===")
    print(f"Report: {args.out / 'backend_comparison.md'}")
    print(f"JSON:   {args.out / 'backend_comparison.json'}")
    for name in EMBEDDERS:
        report = results[name]["end_to_end"]["test"]
        print(
            f"{name}: test answer accuracy={report['answer_accuracy']}%, "
            f"test abstain recall={report['abstain_recall_on_unanswerable']}%, "
            f"p95={report['latency_ms_p95']} ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
