"""The question-answering agent: retrieve -> gate -> answer -> verify -> cite (or abstain)."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .config import Config
from .index import HybridIndex, Hit
from .ingest import Chunk, load_pdf
from .llm import LLM, NOT_FOUND, build_llm
from .text import QSTOP, split_sentences, tokenize

_CITE_RE = re.compile(r"\[S(\d+)\]")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# Why an answer was refused. Stable strings: the UI and eval key off these.
ABSTAIN_REASONS = {
    "low_coverage": "The retrieved passages do not mention enough of the question's key terms.",
    "model_not_found": "The answerer found nothing in the retrieved passages that answers the question.",
    "no_valid_citation": "The answer had no valid citation, so it was rejected.",
    "unsupported_number": "The answer contained a number that does not appear in the cited passages.",
}


@dataclass
class Citation:
    source_id: int        # the [S#] label used in the answer text
    chunk_id: int
    section: str
    pages: list[int]
    quote: str            # best-matching sentence inside the cited chunk


@dataclass
class Answer:
    question: str
    text: str
    found: bool
    citations: list[Citation] = field(default_factory=list)
    reason: str | None = None          # set when found is False
    coverage: float = 0.0
    retrieved: list[Hit] = field(default_factory=list, repr=False)
    latency_ms: float = 0.0
    rewritten_query: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["retrieved"] = [
            {"chunk_id": h.chunk.id, "section": h.chunk.section, "pages": h.chunk.pages, "score": h.score,
             "bm25_rank": h.bm25_rank, "dense_rank": h.dense_rank}
            for h in self.retrieved
        ]
        return d


class PaperQAAgent:
    def __init__(self, chunks: list[Chunk], config: Config | None = None, llm: LLM | None = None,
                 index: HybridIndex | None = None) -> None:
        self.config = config or Config()
        self.chunks = chunks
        self.index = index or HybridIndex(chunks, config=self.config)
        self.llm = llm or build_llm(self.config, self.index.idf)

    @classmethod
    def from_pdf(cls, path: str | Path, config: Config | None = None, llm: LLM | None = None) -> "PaperQAAgent":
        config = config or Config()
        return cls(load_pdf(path, config), config, llm)

    # ------------------------------------------------------------------ helpers
    def coverage(self, question: str, hits: list[Hit]) -> float:
        """IDF-weighted share of the question's content terms that appear in the retrieved passages.

        Terms that never occur in the paper get the maximum weight, so a question about something the
        paper does not discuss scores low even if generic words ('experiments') match.
        """
        terms = set(tokenize(question, stop=QSTOP))
        if not terms:
            return 1.0
        present: set[str] = set()
        for h in hits:
            present |= set(tokenize(h.chunk.embed_text))
        weights = {t: self.index.idf(t) for t in terms}
        return sum(w for t, w in weights.items() if t in present) / sum(weights.values())

    @staticmethod
    def _best_quote(chunk: Chunk, answer_text: str) -> str:
        target = set(tokenize(answer_text))
        best, best_score = chunk.text, -1.0
        for sent in split_sentences(chunk.text):
            toks = set(tokenize(sent))
            score = len(toks & target) / (len(toks) or 1)
            if score > best_score:
                best, best_score = sent, score
        return best

    def _abstain(self, q: str, reason: str, hits: list[Hit], cov: float, t0: float, rewritten: str | None) -> Answer:
        return Answer(q, "I could not find an answer to this in the paper.", False, [], reason, cov, hits,
                      (time.perf_counter() - t0) * 1000, rewritten)

    # ------------------------------------------------------------------ main entry point
    def ask(self, question: str) -> Answer:
        t0 = time.perf_counter()
        hits = self.index.search(question)
        cov = self.coverage(question, hits)
        rewritten = None

        # Agentic step: if the first retrieval looks weak and the LLM can paraphrase, try one rewritten query.
        if cov < self.config.min_coverage and self.config.allow_query_rewrite and self.llm.supports_rewrite:
            rewritten = self.llm.rewrite(question)
            hits2 = self.index.search(f"{question} {rewritten}")
            cov2 = self.coverage(f"{question} {rewritten}", hits2)
            if cov2 > cov:
                hits, cov = hits2, cov2
        # Retrieval gate. The extractive answerer cannot judge semantics, so it gets the strict threshold.
        # An LLM can itself answer NOT_FOUND, so it only needs the gate to cut off clearly off-topic questions
        # (which saves an API call) and gets a looser floor so paraphrased questions are not refused up front.
        floor = self.config.min_coverage if not self.llm.supports_rewrite else self.config.min_coverage * 0.5
        if cov < floor:
            return self._abstain(question, "low_coverage", hits, cov, t0, rewritten)

        raw = self.llm.answer(question, hits).strip()
        if not raw or raw.upper().startswith(NOT_FOUND):
            return self._abstain(question, "model_not_found", hits, cov, t0, rewritten)

        ids = [int(i) for i in _CITE_RE.findall(raw)]
        valid = [i for i in dict.fromkeys(ids) if 1 <= i <= len(hits)]
        if not valid:
            return self._abstain(question, "no_valid_citation", hits, cov, t0, rewritten)

        # Hallucination guard: every number in the answer must be present in the cited passages.
        body = _CITE_RE.sub("", raw)
        cited_text = " ".join(hits[i - 1].chunk.text for i in valid)
        cited_numbers = set(_NUM_RE.findall(cited_text))
        if any(n not in cited_numbers for n in _NUM_RE.findall(body)):
            return self._abstain(question, "unsupported_number", hits, cov, t0, rewritten)

        citations = [
            Citation(i, hits[i - 1].chunk.id, hits[i - 1].chunk.section, hits[i - 1].chunk.pages,
                     self._best_quote(hits[i - 1].chunk, body))
            for i in valid
        ]
        return Answer(question, raw, True, citations, None, cov, hits, (time.perf_counter() - t0) * 1000, rewritten)
