from __future__ import annotations

import json
from pathlib import Path

from src.core.io import ArtifactWriter, ObservabilityService, WorkspaceManager


def test_write_node_execution_snapshot_writes_meta_artifact(tmp_path: Path) -> None:
    workspace = WorkspaceManager(jobs_root=tmp_path / "data/jobs")
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)

    state = {
        "source": "tu_berlin",
        "job_id": "job-1",
        "run_id": "run-1",
        "current_node": "match",
        "status": "running",
        "artifact_refs": {"last_proposed_state_ref": "nodes/match/approved/state.json"},
    }
    written = service.write_node_execution_snapshot(node_name="match", state=state)

    assert written is not None
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["node"] == "match"
    assert payload["job_id"] == "job-1"
    assert payload["artifact_refs"]["last_proposed_state_ref"].endswith("state.json")


def test_write_run_summary_writes_graph_summary_artifact(tmp_path: Path) -> None:
    workspace = WorkspaceManager(jobs_root=tmp_path / "data/jobs")
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)

    state = {
        "source": "tu_berlin",
        "job_id": "job-1",
        "run_id": "run-1",
        "current_node": "package",
        "status": "completed",
    }
    written = service.write_run_summary(state)

    assert written is not None
    assert written == tmp_path / "data/jobs/tu_berlin/job-1/graph/run_summary.json"
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["current_node"] == "package"
    assert payload["status"] == "completed"
