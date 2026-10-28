"""Command line interface:  python -m paperqa {ask,chat,chunks,eval} ..."""
from __future__ import annotations

import argparse
import json
import sys

from .agent import Answer, PaperQAAgent
from .config import Config


def _config(args) -> Config:
    cfg = Config()
    cfg.embedder = getattr(args, "embedder", cfg.embedder)
    cfg.llm = getattr(args, "llm", cfg.llm)
    cfg.top_k = getattr(args, "top_k", cfg.top_k)
    return cfg


def format_answer(a: Answer) -> str:
    out = [a.text]
    if a.found:
        out.append("")
        for c in a.citations:
            pages = ", ".join(map(str, c.pages))
            out.append(f"  [S{c.source_id}] Section {c.section} (p. {pages}): \"{c.quote}\"")
    else:
        out.append(f"  (reason: {a.reason}; coverage {a.coverage:.2f})")
    out.append(f"  [{a.latency_ms:.0f} ms]")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="paperqa", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("pdf")
        sp.add_argument("--embedder", choices=["lsa", "st"], default="lsa")
        sp.add_argument("--llm", choices=["auto", "anthropic", "extractive"], default="auto")
        sp.add_argument("--top-k", type=int, default=5, dest="top_k")

    a = sub.add_parser("ask", help="ask one question"); common(a); a.add_argument("question"); a.add_argument("--json", action="store_true")
    c = sub.add_parser("chat", help="interactive Q&A"); common(c)
    k = sub.add_parser("chunks", help="inspect how the PDF was chunked"); common(k)
    e = sub.add_parser("eval", help="run the evaluation set"); common(e)
    e.add_argument("--eval-set", default="eval/eval_set.json"); e.add_argument("--out", default="results")

    args = p.parse_args(argv)
    agent = PaperQAAgent.from_pdf(args.pdf, _config(args))

    if args.cmd == "ask":
        ans = agent.ask(args.question)
        print(json.dumps(ans.to_dict(), indent=1) if args.json else format_answer(ans))
    elif args.cmd == "chat":
        print(f"Loaded {len(agent.chunks)} chunks. Ask a question (empty line or Ctrl-D to quit).")
        while True:
            try:
                q = input("\n? ").strip()
            except EOFError:
                break
            if not q:
                break
            print(format_answer(agent.ask(q)))
    elif args.cmd == "chunks":
        for ch in agent.chunks:
            print(f"#{ch.id:<3} p{ch.pages} {ch.section} ({ch.n_words}w): {ch.text[:100]}...")
    elif args.cmd == "eval":
        from .evaluate import run, render_markdown

        result = run(args.pdf, args.eval_set, args.out, agent)
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
