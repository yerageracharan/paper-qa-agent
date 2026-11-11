import numpy as np
import pytest

from paperqa.config import Config
from paperqa.index import BM25, HybridIndex
from paperqa.text import tokenize


def test_bm25_prefers_rare_matching_term():
    docs = [tokenize(t) for t in ["adapters adapters adapters layer", "hard concrete gate", "layer layer layer"]]
    bm = BM25(docs)
    scores = bm.scores(tokenize("hard concrete"))
    assert int(np.argmax(scores)) == 1
    assert scores[0] == 0 and scores[2] == 0


def test_search_finds_the_evidence_chunk(chunks):
    idx = HybridIndex(chunks, config=Config())
    top = idx.search("what bottleneck dimension do the adapters use", k=3)
    assert "r = 32" in top[0].chunk.text or any("r = 32" in h.chunk.text for h in top)
    assert [h.rank for h in top] == [1, 2, 3]


@pytest.mark.parametrize("mode", ["bm25", "dense", "hybrid"])
def test_all_modes_return_ranked_hits(chunks, mode):
    idx = HybridIndex(chunks, config=Config())
    hits = idx.search("sparsity coefficient lambda", k=4, mode=mode)
    assert 1 <= len(hits) <= 4
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_unknown_terms_get_max_idf(chunks):
    idx = HybridIndex(chunks, config=Config())
    assert idx.idf("zzzunseen") >= max(idx.bm25.idf.values())
    assert not idx.vocab_has("zzzunseen")


def test_empty_document_is_rejected():
    with pytest.raises(ValueError):
        HybridIndex([], config=Config())


def test_invalid_mode(chunks):
    with pytest.raises(ValueError):
        HybridIndex(chunks).search("x", mode="nope")


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_search_rejects_invalid_result_limits(chunks, k):
    idx = HybridIndex(chunks, config=Config())
    with pytest.raises(ValueError, match="k must be a positive integer"):
        idx.search("adapter evidence", k=k)


def test_search_uses_configured_limit_when_k_is_none(chunks):
    idx = HybridIndex(chunks, config=Config(top_k=2))
    assert len(idx.search("adapter evidence")) <= 2


def test_search_returns_empty_for_blank_query(chunks):
    idx = HybridIndex(chunks, config=Config())
    assert idx.search("   ") == []
