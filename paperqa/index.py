"""Hybrid retrieval: BM25 (lexical) + dense embeddings (semantic) fused with reciprocal rank fusion."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .config import Config
from .ingest import Chunk
from .text import tokenize


# ----------------------------------------------------------------------------- BM25
class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs = docs
        self.avgdl = sum(len(d) for d in docs) / max(len(docs), 1)
        self.tf = [self._count(d) for d in docs]
        df: dict[str, int] = {}
        for d in self.tf:
            for term in d:
                df[term] = df.get(term, 0) + 1
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    @staticmethod
    def _count(doc: list[str]) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in doc:
            out[t] = out.get(t, 0) + 1
        return out

    def scores(self, query: list[str]) -> np.ndarray:
        out = np.zeros(len(self.docs))
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            for term in set(query):
                f = tf.get(term)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                out[i] += self.idf[term] * f * (self.k1 + 1) / denom
        return out


# ----------------------------------------------------------------------------- embedders
class Embedder(Protocol):
    def fit(self, texts: list[str]) -> None: ...
    def encode(self, texts: list[str]) -> np.ndarray: ...  # L2-normalised rows


class LsaEmbedder:
    """Offline 'embedding': TF-IDF (uni+bi-grams) -> truncated SVD (latent semantic analysis).

    Needs no model download, so the whole pipeline is reproducible offline. It captures word
    co-occurrence within the paper but NOT real-world semantics; use SentenceTransformerEmbedder for that.
    """

    def __init__(self, dims: int = 64) -> None:
        self.dims = dims
        self.vectorizer = None
        self.svd = None

    def fit(self, texts: list[str]) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(
            tokenizer=tokenize, lowercase=False, token_pattern=None, ngram_range=(1, 2), sublinear_tf=True
        )
        matrix = self.vectorizer.fit_transform(texts)
        n_comp = max(2, min(self.dims, matrix.shape[0] - 1, matrix.shape[1] - 1))
        self.svd = TruncatedSVD(n_components=n_comp, random_state=0)
        self.svd.fit(matrix)

    def encode(self, texts: list[str]) -> np.ndarray:
        assert self.vectorizer is not None and self.svd is not None, "call fit() first"
        vecs = self.svd.transform(self.vectorizer.transform(texts))
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.where(norms == 0, 1, norms)


class SentenceTransformerEmbedder:
    """Real neural embeddings (optional dependency: `pip install sentence-transformers`)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def fit(self, texts: list[str]) -> None:  # pretrained: nothing to fit
        return None

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False))


def get_embedder(config: Config) -> Embedder:
    if config.embedder == "st":
        return SentenceTransformerEmbedder(config.st_model)
    return LsaEmbedder(config.lsa_dims)


# ----------------------------------------------------------------------------- index
@dataclass
class Hit:
    chunk: Chunk
    score: float                 # fused (RRF) score, or the single-mode score
    rank: int                    # 1-based rank in the final list
    bm25: float = 0.0
    dense: float = 0.0
    bm25_rank: int | None = None
    dense_rank: int | None = None


class HybridIndex:
    def __init__(self, chunks: list[Chunk], embedder: Embedder | None = None, config: Config | None = None) -> None:
        if not chunks:
            raise ValueError("No text could be extracted from the document (is it a scanned PDF?).")
        self.config = config or Config()
        self.chunks = chunks
        texts = [c.embed_text for c in chunks]
        self.tokens = [tokenize(t) for t in texts]
        self.bm25 = BM25(self.tokens)
        self.embedder = embedder or get_embedder(self.config)
        self.embedder.fit(texts)
        self.matrix = self.embedder.encode(texts)
        self._max_idf = math.log(1 + (len(chunks) + 0.5) / 0.5)

    def idf(self, term: str) -> float:
        """Rarity weight of a term. Terms absent from the paper get the maximum weight."""
        return self.bm25.idf.get(term, self._max_idf)

    def vocab_has(self, term: str) -> bool:
        return term in self.bm25.idf

    def search(self, query: str, k: int | None = None, mode: str = "hybrid") -> list[Hit]:
        k = k or self.config.top_k
        q_tokens = tokenize(query)
        bm = self.bm25.scores(q_tokens)
        dense = self.matrix @ self.embedder.encode([query])[0]

        bm_order = [i for i in np.argsort(-bm) if bm[i] > 0]
        de_order = [i for i in np.argsort(-dense) if dense[i] > 1e-9]
        bm_rank = {int(i): r + 1 for r, i in enumerate(bm_order)}
        de_rank = {int(i): r + 1 for r, i in enumerate(de_order)}

        if mode == "bm25":
            fused = {i: float(bm[i]) for i in bm_rank}
        elif mode == "dense":
            fused = {i: float(dense[i]) for i in de_rank}
        elif mode == "hybrid":
            fused = {}
            for ranks in (bm_rank, de_rank):
                for i, r in ranks.items():
                    fused[i] = fused.get(i, 0.0) + 1.0 / (self.config.rrf_k + r)
        else:
            raise ValueError(f"unknown mode {mode!r}")

        top = sorted(fused, key=lambda i: -fused[i])[:k]
        return [
            Hit(self.chunks[i], fused[i], r + 1, float(bm[i]), float(dense[i]), bm_rank.get(i), de_rank.get(i))
            for r, i in enumerate(top)
        ]
