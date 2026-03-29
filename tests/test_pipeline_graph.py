"""Tests for the top-level pipeline graph."""

import asyncio

import pytest
from src.graph import (
    GraphState,
    build_pipeline_graph,
    create_studio_graph,
)
from src.core.data_manager import DataManager
from src.graph.nodes.ingest import make_ingest_node


def test_graph_state_typing():
    """Verify GraphState accepts expected fields."""
    state: GraphState = {
        "source": "test",
        "job_id": "123",
        "run_id": "run-001",
        "current_node": "ingest",
        "status": "pending",
        "artifact_refs": {
            "ingest_state": "data/jobs/test/123/nodes/ingest/proposed/state.json"
        },
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
    assert "ingest" in nodes
    assert "translate" in nodes
    assert "extract_bridge" in nodes
    assert "match_skill" in nodes
    assert "generate_documents" in nodes
    assert "render" in nodes
    assert "package" in nodes


def test_pipeline_accepts_valid_source():
    """Verify the pipeline accepts valid source names."""
    from src.graph import build_pipeline_graph, GraphState
    from src.scraper.main import PROVIDERS

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


def test_ingest_node_reuses_existing_canonical_artifact(tmp_path):
    manager = DataManager(tmp_path / "data" / "jobs")
    manager.ingest_raw_job(
        source="stepstone",
        job_id="123",
        payload={"job_title": "Engineer"},
        content="# Job",
    )
    node = make_ingest_node(manager)

    result = asyncio.run(
        node({"source": "stepstone", "job_id": "123", "artifact_refs": {}})
    )

    assert result["status"] == "running"
    assert result["current_node"] == "ingest"
    assert "ingest_state" in result["artifact_refs"]


def test_ingest_node_fetches_single_job_from_source_url(tmp_path, monkeypatch):
    manager = DataManager(tmp_path / "data" / "jobs")
    node = make_ingest_node(manager)

    class FakeAdapter:
        async def fetch_job(self, url: str) -> str:
            manager.ingest_raw_job(
                source="stepstone",
                job_id="555",
                payload={"job_title": "Fetched"},
            )
            return "555"

    monkeypatch.setattr(
        "src.graph.nodes.ingest.build_providers",
        lambda data_manager: {"stepstone": FakeAdapter()},
    )

    result = asyncio.run(
        node(
            {
                "source": "stepstone",
                "source_url": "https://example.test/job-555",
                "artifact_refs": {},
            }
        )
    )

    assert result["status"] == "running"
    assert result["job_id"] == "555"
    assert manager.has_ingested_job("stepstone", "555") is True
