from __future__ import annotations

from src.core.api_client import (
    _derive_thread_status,
    _next_review_node,
    _normalize_run_result,
)


def test_next_review_node_returns_first_hitl_node() -> None:
    next_nodes = ["hitl_2_blueprint_logic", "other_node"]

    assert _next_review_node(next_nodes) == "hitl_2_blueprint_logic"


def test_next_review_node_returns_none_without_hitl_node() -> None:
    assert _next_review_node(["assembler", "profile_updater"]) is None
    assert _next_review_node([]) is None
    assert _next_review_node(None) is None


def test_next_review_node_accepts_outer_stage_review_nodes() -> None:
    assert _next_review_node(["stage_2_semantic_bridge"]) == "stage_2_semantic_bridge"


def test_derive_thread_status_marks_pending_review() -> None:
    state = {"next": ["stage_2_semantic_bridge"], "values": {"status": "running"}}

    assert _derive_thread_status(state) == "pending_review"


def test_derive_thread_status_marks_failed_when_error_present() -> None:
    state = {
        "next": [],
        "values": {"status": "running", "error_state": {"message": "boom"}},
    }

    assert _derive_thread_status(state) == "failed"


def test_normalize_run_result_carries_error_message() -> None:
    state = {"next": [], "values": {"status": "failed"}}

    normalized = _normalize_run_result({}, state, error="403 PERMISSION_DENIED")

    assert normalized["status"] == "failed"
    assert normalized["error"] == "403 PERMISSION_DENIED"
