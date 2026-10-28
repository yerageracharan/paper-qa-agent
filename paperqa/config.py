"""Central configuration. Every value here is a tunable trade-off documented in the README."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Config:
    # --- chunking ---
    chunk_words: int = 120          # soft upper bound on words per chunk
    overlap_sentences: int = 1      # sentences repeated between neighbouring chunks
    exclude_sections: tuple[str, ...] = ("References",)

    # --- retrieval ---
    top_k: int = 5                  # chunks passed to the answerer
    rrf_k: int = 60                 # reciprocal-rank-fusion constant
    embedder: str = "lsa"           # "lsa" (offline) | "st" (sentence-transformers)
    st_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    lsa_dims: int = 64

    # --- abstention ---
    min_coverage: float = 0.3       # idf-weighted share of question terms found in retrieved text
    sentence_coverage: float = 0.3  # same, but required inside the single best answer sentence (offline answerer)

    # --- LLM ---
    llm: str = "auto"               # "auto" | "anthropic" | "extractive"
    model: str = "claude-sonnet-5-5"
    max_tokens: int = 400
    allow_query_rewrite: bool = True

    extra: dict = field(default_factory=dict)
