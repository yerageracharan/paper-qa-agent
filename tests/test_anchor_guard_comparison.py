from scripts.evaluate_anchor_guard import compare_records, render_report


def _record(question_id: str, found: bool, reason: str | None, answerable: bool = True) -> dict:
    return {
        "id": question_id, "question": "What does the paper say?", "answerable": answerable,
        "type": "fact", "found": found, "reason": reason,
    }


def test_compare_records_identifies_new_refusal_and_answer():
    base = [_record("a1", True, None), _record("u1", True, None, False)]
    guarded = [_record("a1", False, "missing_question_anchor"),
               _record("u1", False, "missing_question_anchor", False)]
    result = compare_records(base, guarded)
    assert {row["id"] for row in result["newly_refused"]} == {"a1", "u1"}
    assert result["newly_answered"] == []
    assert len(result["reason_changes"]) == 2


def test_compare_records_rejects_different_question_sets():
    try:
        compare_records([_record("a1", True, None)], [_record("a2", False, "missing_question_anchor")])
    except ValueError as exc:
        assert "different question IDs" in str(exc)
    else:
        raise AssertionError("Expected different question IDs to be rejected")


def test_render_report_shows_guard_caveats_and_metrics():
    metrics = {
        variant: {
            split: {
                "answer_accuracy": 86.7, "false_abstain_rate": 6.7,
                "abstain_recall_on_unanswerable": 50.0,
                "wrong_answer_rate_when_answering": 7.1,
                "citation_hit_rate": 92.9, "latency_ms_p50": 1.0,
                "latency_ms_p95": 1.2,
            }
            for split in ("dev", "test", "all")
        }
        for variant in ("baseline", "strict_question_anchors")
    }
    comparison = {
        "metrics": metrics,
        "record_changes": {
            "newly_refused": [{"id": "u05", "type": "in_topic", "answerable": False,
                               "question": "What accuracy is reported?", "guarded_reason": "missing_question_anchor"}],
            "newly_answered": [],
            "reason_changes": [],
        },
    }
    report = render_report(comparison)
    assert "strict_question_anchors" in report
    assert "Not a semantic entailment model" in report
    assert "u05" in report
