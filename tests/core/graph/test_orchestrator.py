"""Tests for graph orchestration helpers."""

from __future__ import annotations

from typing import cast
from contextlib import contextmanager

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


def test_create_app_wraps_node_handlers_with_trace(monkeypatch) -> None:
    calls: list[str] = []

    @contextmanager
    def fake_trace_section(name: str, metadata=None):
        calls.append(name)
        yield

    class FakeStateGraph:
        def __init__(self, _state_cls):
            self.nodes = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def set_entry_point(self, _entry):
            return None

        def add_edge(self, _src, _dst):
            return None

        def add_conditional_edges(self, _review, _router, _transitions):
            return None

        def compile(self, **_kwargs):
            return self

    monkeypatch.setattr("src.graph.trace_section", fake_trace_section)
    monkeypatch.setattr(
        "src.graph._load_langgraph_primitives",
        lambda: (FakeStateGraph, "__END__"),
    )

    app = create_app(
        node_registry={"scrape": lambda state: state, "package": lambda state: state},
        entry_point="scrape",
        linear_edges=(("scrape", "package"),),
        review_transitions={},
        interrupt_before=(),
    )
    state = cast(
        GraphState,
        {
            "source": "tu_berlin",
            "job_id": "1",
            "run_id": "r1",
            "current_node": "scrape",
            "status": "running",
        },
    )
    app.nodes["scrape"](state)

    assert calls == ["node.scrape"]
