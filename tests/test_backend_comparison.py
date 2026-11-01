from scripts.evaluate_backends import render_comparison


def _result(embedder: str) -> dict:
    return {
        "backend": {"embedder": embedder, "llm": "ExtractiveLLM", "top_k": 5, "chunks": 18},
        "retrieval": {
            "bm25": {"hit@1": 73.9, "hit@3": 91.3, "hit@5": 95.7, "mrr": 0.837},
            "dense": {"hit@1": 82.6, "hit@3": 91.3, "hit@5": 95.7, "mrr": 0.880},
            "hybrid": {"hit@1": 82.6, "hit@3": 91.3, "hit@5": 95.7, "mrr": 0.880},
        },
        "end_to_end": {
            split: {
                "answer_accuracy": 86.7, "false_abstain_rate": 6.7,
                "abstain_recall_on_unanswerable": 50.0,
                "wrong_answer_rate_when_answering": 7.1,
                "citation_hit_rate": 92.9, "latency_ms_p50": 1.3,
                "latency_ms_p95": 1.5,
            }
            for split in ("dev", "test", "all")
        },
    }


def test_render_comparison_contains_both_backends_and_key_metrics():
    report = render_comparison({"lsa": _result("lsa"), "st": _result("st")})
    assert "| lsa | dense | 82.6% | 91.3% | 95.7% | 0.880 |" in report
    assert "| st | hybrid | 82.6% | 91.3% | 95.7% | 0.880 |" in report
    assert "Abstain recall on unanswerable" in report
    assert "one synthetic three-page paper and 29 questions" in report


def test_render_comparison_rejects_mismatched_answerers():
    lsa = _result("lsa")
    st = _result("st")
    st["backend"]["llm"] = "AnthropicLLM"
    try:
        render_comparison({"lsa": lsa, "st": st})
    except ValueError as exc:
        assert "same answerer" in str(exc)
    else:
        raise AssertionError("Expected mismatched answerers to be rejected")
