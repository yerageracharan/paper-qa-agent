"""Answer generators. Both obey the same contract:

    answer(question, sources) -> str   # cited text such as "SGA trains 0.8% of parameters [S1]." or "NOT_FOUND"

* AnthropicLLM  - Claude, instructed to answer only from the numbered excerpts.
* ExtractiveLLM - offline, deterministic: returns the best-matching sentence(s) verbatim. Lets the whole
                  pipeline (and the eval) run with no API key, and makes a useful non-LLM baseline.
"""
from __future__ import annotations

import os
from typing import Callable, Protocol

from .config import Config
from .index import Hit
from .text import QSTOP, split_sentences, tokenize

NOT_FOUND = "NOT_FOUND"

SYSTEM_PROMPT = f"""You answer questions about ONE research paper using ONLY the numbered excerpts provided.
Rules:
1. Every factual statement must end with a citation such as [S2]; several are allowed, e.g. [S1][S3].
2. Use only what the excerpts state. Do not use outside knowledge and do not guess or compute new numbers.
3. If the excerpts do not contain the answer, reply with exactly: {NOT_FOUND}
4. Copy numbers exactly as written. Be concise: 1-4 sentences."""

REWRITE_PROMPT = (
    "Rewrite the user's question as a short keyword-rich search query using terminology likely to appear in a "
    "research paper (synonyms welcome). Output only the query."
)


def format_sources(hits: list[Hit]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        pages = ",".join(map(str, h.chunk.pages))
        blocks.append(f"[S{i}] (Section: {h.chunk.section}; page {pages})\n{h.chunk.text}")
    return "\n\n".join(blocks)


class LLM(Protocol):
    supports_rewrite: bool

    def answer(self, question: str, hits: list[Hit]) -> str: ...
    def rewrite(self, question: str) -> str: ...


class AnthropicLLM:
    supports_rewrite = True

    def __init__(self, config: Config, client=None) -> None:
        if client is None:
            import anthropic  # optional dependency

            client = anthropic.Anthropic()
        self.client = client
        self.config = config

    def _complete(self, system: str, user: str, max_tokens: int) -> str:
        resp = self.client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(b, "text", "") for b in resp.content).strip()

    def answer(self, question: str, hits: list[Hit]) -> str:
        user = f"Excerpts:\n\n{format_sources(hits)}\n\nQuestion: {question}"
        return self._complete(SYSTEM_PROMPT, user, self.config.max_tokens)

    def rewrite(self, question: str) -> str:
        return self._complete(REWRITE_PROMPT, question, 60)


class ExtractiveLLM:
    """Pick the sentence(s) whose rare question terms overlap most; abstain if none covers enough of them."""

    supports_rewrite = False

    def __init__(self, config: Config, idf: Callable[[str], float]) -> None:
        self.config = config
        self.idf = idf

    def _terms(self, question: str) -> list[str]:
        return sorted(set(tokenize(question, stop=QSTOP)))

    def answer(self, question: str, hits: list[Hit]) -> str:
        terms = self._terms(question)
        if not terms:
            return NOT_FOUND
        weights = {t: self.idf(t) for t in terms}
        total = sum(weights.values())
        wants_number = any(w in question.lower() for w in ("how many", "how much", "what percent", "by how", "f1", "accuracy", "fraction"))

        scored = []  # (score, coverage, source_idx, sentence)
        for si, hit in enumerate(hits, 1):
            for sent in split_sentences(hit.chunk.text):
                toks = set(tokenize(sent))
                cov = sum(weights[t] for t in terms if t in toks) / total
                score = cov * (1.0 + (0.25 if wants_number and any(c.isdigit() for c in sent) else 0.0))
                scored.append((score, cov, si, sent))
        if not scored:
            return NOT_FOUND
        scored.sort(key=lambda s: (-s[0], s[2]))
        best = scored[0]
        if best[1] < self.config.sentence_coverage:
            return NOT_FOUND

        picked = [best]
        for cand in scored[1:]:
            if len(picked) == 2:
                break
            if cand[2] != best[2] and cand[1] >= self.config.sentence_coverage and cand[0] >= 0.8 * best[0]:
                picked.append(cand)
        return " ".join(f"{s[3].rstrip()} [S{s[2]}]" for s in picked)

    def rewrite(self, question: str) -> str:
        return question


def build_llm(config: Config, idf: Callable[[str], float]) -> LLM:
    choice = config.llm
    if choice == "auto":
        choice = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "extractive"
        if choice == "anthropic":
            try:
                import anthropic  # noqa: F401
            except ImportError:
                choice = "extractive"
    if choice == "anthropic":
        return AnthropicLLM(config)
    return ExtractiveLLM(config, idf)
