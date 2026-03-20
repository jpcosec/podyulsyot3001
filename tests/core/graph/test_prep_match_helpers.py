"""Tests for prep-match graph helper functions."""

from __future__ import annotations

from typing import cast

from src.core.graph.state import GraphState
from src.graph import (
    PREP_MATCH_LINEAR_EDGES,
    PREP_MATCH_REVIEW_TRANSITIONS,
    build_prep_match_node_registry,
    create_prep_match_app,
    run_prep_match,
)


def test_build_prep_match_node_registry_contains_required_nodes() -> None:
    registry = build_prep_match_node_registry()
    assert set(registry) == {
        "scrape",
        "translate_if_needed",
        "extract_understand",
        "match",
        "review_match",
        "generate_documents",
        "render",
        "package",
    }


def test_create_prep_match_app_delegates_expected_topology(monkeypatch) -> None:
    captured = {}

    def fake_create_app(**kwargs):
        captured.update(kwargs)
        return "compiled"

    monkeypatch.setattr("src.graph.create_app", fake_create_app)

    out = create_prep_match_app(checkpointer="cp", interrupt_before=("review_match",))
    assert out == "compiled"
    assert captured["entry_point"] == "scrape"
    assert captured["linear_edges"] == PREP_MATCH_LINEAR_EDGES
    assert captured["review_transitions"] == PREP_MATCH_REVIEW_TRANSITIONS
    assert (
        captured["review_transitions"]["review_match"]["approve"]
        == "generate_documents"
    )


def test_run_prep_match_uses_thread_id_and_resume_behavior(monkeypatch) -> None:
    class FakeApp:
        def __init__(self):
            self.calls = []

        def invoke(self, payload, config=None):
            self.calls.append((payload, config))
            return {"ok": True}

    app = FakeApp()
    monkeypatch.setattr("src.graph.create_prep_match_app", lambda **kwargs: app)

    state = {
        "source": "tu_berlin",
        "job_id": "201397",
        "run_id": "r1",
        "current_node": "scrape",
        "status": "running",
    }

    typed_state = cast(GraphState, state)
    run_prep_match(typed_state, resume=False)
    run_prep_match(typed_state, resume=True)

    first_payload, first_config = app.calls[0]
    second_payload, second_config = app.calls[1]

    assert first_payload["job_id"] == "201397"
    assert first_config["configurable"]["thread_id"] == "tu_berlin_201397"
    assert second_payload is None
    assert second_config["configurable"]["thread_id"] == "tu_berlin_201397"
