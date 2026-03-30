"""Tests for the top-level pipeline graph."""

import inspect

import pytest
from src.graph import (
    GraphState,
    build_pipeline_graph,
    create_studio_graph,
)
from src.core.data_manager import DataManager
from src.graph import make_extract_bridge_node
from src.graph.nodes.generate_documents import make_generate_documents_node
from src.graph.nodes.ingest import make_ingest_node
from src.graph.nodes.load_profile import make_load_profile_node
from src.graph.nodes.package import make_package_node
from src.graph.nodes.render import make_render_node
from src.graph.nodes.translate import make_translate_node


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


def test_top_level_pipeline_nodes_are_sync(tmp_path):
    manager = DataManager(tmp_path / "data" / "jobs")

    nodes = [
        make_ingest_node(manager),
        make_translate_node(manager),
        make_extract_bridge_node(manager),
        make_load_profile_node(manager),
        make_generate_documents_node(manager),
        make_render_node(manager),
        make_package_node(manager),
    ]

    assert all(not inspect.iscoroutinefunction(node) for node in nodes)


def test_ingest_node_reuses_existing_canonical_artifact(tmp_path):
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


def test_extract_bridge_skips_when_upstream_failed(tmp_path):
    """extract_bridge must return status=failed immediately if upstream status is failed."""
    from src.graph import _extract_bridge_node
    from unittest.mock import MagicMock
    from src.core.data_manager import DataManager

    dm = MagicMock(spec=DataManager)
    state = {
        "source": "test",
        "job_id": "999",
        "status": "failed",
        "error_state": {"node": "translate", "message": "artifact missing", "details": None},
        "artifact_refs": {},
    }
    result = _extract_bridge_node(state, dm)

    assert result["status"] == "failed"
    assert result["current_node"] == "extract_bridge"
    assert "translate" in result["error_state"]["message"]


def test_extract_bridge_fails_on_missing_translate_artifact(tmp_path):
    """extract_bridge must return status=failed with actionable message when translate artifact missing."""
    from src.graph import _extract_bridge_node
    from unittest.mock import MagicMock
    from src.core.data_manager import DataManager

    dm = MagicMock(spec=DataManager)
    dm.read_json_artifact.side_effect = FileNotFoundError("not found")
    state = {
        "source": "test",
        "job_id": "999",
        "status": "running",
        "artifact_refs": {},
    }
    result = _extract_bridge_node(state, dm)

    assert result["status"] == "failed"
    assert result["current_node"] == "extract_bridge"
    assert "translate" in result["error_state"]["message"].lower()


def test_translate_single_job_skips_when_already_translated(tmp_path):
    """translate_single_job must skip and return True when output files already exist."""
    from unittest.mock import MagicMock
    from src.core.tools.translator.main import translate_single_job
    from src.core.data_manager import DataManager

    ingest_json = tmp_path / "ingest_state.json"
    ingest_json.write_text('{"job_title": "Test", "original_language": "de"}')
    out_json = tmp_path / "translate_state.json"
    out_json.write_text("{}")  # already exists

    dm = MagicMock(spec=DataManager)

    def _artifact_path(source, job_id, node_name, stage, filename):
        if node_name == "ingest":
            return ingest_json
        return out_json  # translate output already exists

    dm.artifact_path.side_effect = _artifact_path

    adapter = MagicMock()
    result = translate_single_job(dm, adapter, "test", "job1", target_lang="en", force=False)
    assert result is True
    adapter.translate_fields.assert_not_called()


def test_translate_single_job_translates_non_english(tmp_path):
    """translate_single_job must call translation for non-English jobs."""
    import json
    from unittest.mock import MagicMock
    from src.core.tools.translator.main import translate_single_job
    from src.core.data_manager import DataManager

    ingest_json = tmp_path / "ingest_state.json"
    ingest_json.write_text(json.dumps({"job_title": "Ingenieur", "original_language": "de"}))
    ingest_md = tmp_path / "content.md"
    ingest_md.write_text("Beschreibung")
    out_json = tmp_path / "translate_state.json"
    out_md = tmp_path / "translate_content.md"
    # out files do NOT exist yet

    dm = MagicMock(spec=DataManager)

    def _artifact_path(source, job_id, node_name, stage, filename):
        if node_name == "ingest":
            return ingest_json if filename == "state.json" else ingest_md
        return out_json if filename == "state.json" else out_md

    dm.artifact_path.side_effect = _artifact_path

    adapter = MagicMock()
    translated = {"job_title": "Engineer", "original_language": "en"}
    adapter.translate_fields.return_value = translated

    result = translate_single_job(dm, adapter, "test", "job1", target_lang="en", force=False)
    assert result is True
    adapter.translate_fields.assert_called_once()
