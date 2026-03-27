"""Tests for prep-match quality verification helpers."""

from __future__ import annotations

from src.core.ai.verification import evaluate_prep_match_run


def test_evaluate_prep_match_run_passes_pending_review() -> None:
    initial = {"source": "tu_berlin", "job_id": "201399"}
    output = {
        "status": "pending_review",
        "current_node": "review_match",
        "error_state": None,
    }

    report = evaluate_prep_match_run(initial, output)

    assert report["passed"] is True
    assert report["score"] == 1.0


def test_evaluate_prep_match_run_fails_invalid_status() -> None:
    initial = {"source": "tu_berlin", "job_id": "201399"}
    output = {
        "status": "failed",
        "current_node": "match",
        "error_state": {"failure_type": "INTERNAL_ERROR"},
    }

    report = evaluate_prep_match_run(initial, output)

    assert report["passed"] is False
    assert report["score"] < 1.0
    assert any(item["name"] == "status_allowed" for item in report["checks"])
