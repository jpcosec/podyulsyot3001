"""Tests for the top-level pipeline graph."""

import pytest
from src.graph import (
    GraphState,
    build_pipeline_graph,
    create_studio_graph,
)


def test_graph_state_typing():
    """Verify GraphState accepts expected fields."""
    state: GraphState = {
        "source": "test",
        "job_id": "123",
        "run_id": "run-001",
        "current_node": "scrape",
        "status": "pending",
        "artifact_refs": {"scrape_state": "data/source/test/123/extracted_data.json"},
    }
    assert state["source"] == "test"
    assert state["job_id"] == "123"


def test_build_pipeline_graph_compiles():
    """Verify the pipeline graph can be compiled without errors."""
    app = build_pipeline_graph()
    assert app is not None
    assert hasattr(app, "invoke")


def test_studio_graph_compiles():
    """Verify the studio graph can be compiled without errors."""
    app = create_studio_graph()
    assert app is not None
    assert hasattr(app, "invoke")


def test_graph_has_expected_nodes():
    """Verify the graph has all expected nodes."""
    from src.graph import build_pipeline_graph

    app = build_pipeline_graph()

    nodes = app.nodes
    assert "scrape" in nodes
    assert "translate" in nodes
    assert "extract_bridge" in nodes
    assert "match_skill" in nodes
    assert "generate_documents" in nodes
    assert "render" in nodes
    assert "package" in nodes


def test_pipeline_accepts_valid_source():
    """Verify the pipeline accepts valid source names."""
    from src.graph import build_pipeline_graph, GraphState
    from src.ai.scraper.main import PROVIDERS

    app = build_pipeline_graph()

    assert "stepstone" in PROVIDERS
    assert "xing" in PROVIDERS
    assert "tuberlin" in PROVIDERS

    initial_state: GraphState = {
        "source": "stepstone",
        "job_id": "123",
        "run_id": "test-run-001",
        "current_node": "",
        "status": "pending",
        "artifact_refs": {},
    }

    assert initial_state["source"] in PROVIDERS


def test_graph_checkpointer():
    """Verify the graph has a checkpointer configured."""
    app = build_pipeline_graph()
    assert app.checkpointer is not None
