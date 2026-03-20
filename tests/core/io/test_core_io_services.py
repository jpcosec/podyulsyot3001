from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.io import (
    ArtifactReader,
    ArtifactWriter,
    ProvenanceService,
    WorkspaceManager,
)


def test_workspace_manager_builds_node_stage_artifact() -> None:
    manager = WorkspaceManager()
    path = manager.node_stage_artifact(
        source="tu_berlin",
        job_id="201399",
        node_name="match",
        stage="approved",
        filename="state.json",
    )
    assert path == Path("data/jobs/tu_berlin/201399/nodes/match/approved/state.json")


def test_workspace_manager_rejects_path_escape() -> None:
    manager = WorkspaceManager()
    with pytest.raises(ValueError, match="must not contain"):
        manager.resolve_under_job("tu_berlin", "201399", "../outside.json")


def test_artifact_writer_and_reader_roundtrip(tmp_path: Path) -> None:
    manager = WorkspaceManager(jobs_root=tmp_path / "data/jobs")
    writer = ArtifactWriter(manager)
    reader = ArtifactReader(manager)

    written = writer.write_node_stage_json(
        source="tu_berlin",
        job_id="201399",
        node_name="match",
        stage="approved",
        filename="state.json",
        payload={"decision": "approve", "score": 0.81},
    )
    assert written.exists()
    payload = reader.read_node_stage_json(
        source="tu_berlin",
        job_id="201399",
        node_name="match",
        stage="approved",
        filename="state.json",
    )
    assert payload == {"decision": "approve", "score": 0.81}


def test_provenance_sha256_file_matches_content(tmp_path: Path) -> None:
    file_path = tmp_path / "artifact.json"
    file_path.write_text(json.dumps({"x": 1}, sort_keys=True), encoding="utf-8")
    file_hash = ProvenanceService.sha256_file(file_path)
    direct_hash = ProvenanceService.sha256_text('{"x": 1}')
    assert file_hash == direct_hash
