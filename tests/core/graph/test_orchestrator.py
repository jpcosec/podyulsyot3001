"""Tests for graph orchestration helpers."""

from __future__ import annotations

from typing import cast

import pytest

from src.core.graph.state import GraphState
from src.graph import (
    DEFAULT_ENTRY_POINT,
    DEFAULT_LINEAR_EDGES,
    _route_review_decision,
    create_app,
)


def test_route_review_decision_accepts_valid_values() -> None:
    assert _route_review_decision(_state_with_decision("approve")) == "approve"
    assert (
        _route_review_decision(_state_with_decision("request_regeneration"))
        == "request_regeneration"
    )
    assert _route_review_decision(_state_with_decision("reject")) == "reject"


def test_route_review_decision_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="review_decision"):
        _route_review_decision(cast(GraphState, _state_with_decision("invalid")))


def test_create_app_fails_fast_when_required_nodes_missing() -> None:
    with pytest.raises(ValueError, match="node_registry missing required nodes"):
        create_app(node_registry={})


def test_default_flow_starts_with_ingestion_stages() -> None:
    assert DEFAULT_ENTRY_POINT == "scrape"
    assert ("scrape", "translate_if_needed") in DEFAULT_LINEAR_EDGES
    assert ("translate_if_needed", "extract_understand") in DEFAULT_LINEAR_EDGES
    assert ("match", "review_match") in DEFAULT_LINEAR_EDGES


def _state_with_decision(decision: str) -> GraphState:
    return cast(
        GraphState,
        {
            "source": "linkedin",
            "job_id": "job-1",
            "run_id": "run-1",
            "current_node": "review_match",
            "status": "pending_review",
            "review_decision": decision,
        },
    )
