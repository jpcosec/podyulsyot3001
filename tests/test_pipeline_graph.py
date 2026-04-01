"""Tests for the top-level pipeline graph."""

from __future__ import annotations

import inspect

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.graph import build_pipeline_graph, create_studio_graph
from src.graph.nodes.generate_documents import make_generate_documents_node
from src.graph.nodes.ingest import make_ingest_node
from src.graph.nodes.package import make_package_node
from src.graph.nodes.render import make_render_node


def test_graph_state_typing() -> None:
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


def test_build_pipeline_graph_compiles() -> None:
    app = build_pipeline_graph()
    assert app is not None
    assert hasattr(app, "invoke")


def test_studio_graph_compiles() -> None:
    app = create_studio_graph()
    assert app is not None
    assert hasattr(app, "invoke")


def test_graph_has_expected_nodes() -> None:
    app = build_pipeline_graph()
    nodes = app.nodes
    assert "ingest" in nodes
    assert "generate_documents" in nodes
    assert "render" in nodes
    assert "package" in nodes


def test_graph_checkpointer() -> None:
    app = build_pipeline_graph()
    assert app.checkpointer is not None


def test_top_level_pipeline_nodes_are_sync(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    nodes = [
        make_ingest_node(manager),
        make_generate_documents_node(manager),
        make_render_node(manager),
        make_package_node(manager),
    ]
    assert all(not inspect.iscoroutinefunction(node) for node in nodes)


def test_ingest_node_reuses_existing_canonical_artifact(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    manager.ingest_raw_job(
        source="stepstone",
        job_id="123",
        payload={"job_title": "Engineer"},
        content="# Job",
    )
    node = make_ingest_node(manager)
    result = node({"source": "stepstone", "job_id": "123", "artifact_refs": {}})
    assert result["status"] == "running"
    assert result["current_node"] == "ingest"
    assert "ingest_state" in result["artifact_refs"]


def test_ingest_node_fetches_single_job_from_source_url(tmp_path, monkeypatch) -> None:
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

    result = node(
        {
            "source": "stepstone",
            "source_url": "https://example.test/job-555",
            "artifact_refs": {},
        }
    )
    assert result["status"] == "running"
    assert result["job_id"] == "555"
    assert manager.has_ingested_job("stepstone", "555") is True
