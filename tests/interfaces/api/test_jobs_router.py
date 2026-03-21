from __future__ import annotations

import json
from pathlib import Path

from src.interfaces.api.routers.jobs import (
    document_payload,
    editor_state,
    stage_outputs,
    update_document_payload,
    update_editor_state,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_editor_state_reads_extract_state(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "jobs"
    monkeypatch.setenv("PHD2_DATA_ROOT", str(data_root))
    _write_json(
        data_root
        / "tu_berlin"
        / "201001"
        / "nodes"
        / "extract_understand"
        / "approved"
        / "state.json",
        {"job_title": "Role"},
    )

    payload = editor_state("tu_berlin", "201001", "extract_understand")
    assert payload["node_name"] == "extract_understand"
    assert payload["state"]["job_title"] == "Role"


def test_editor_state_overwrites_match_state(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "jobs"
    monkeypatch.setenv("PHD2_DATA_ROOT", str(data_root))
    job_root = data_root / "tu_berlin" / "201002"
    job_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        job_root / "nodes" / "match" / "approved" / "state.json",
        {"matches": []},
    )

    payload = update_editor_state(
        "tu_berlin",
        "201002",
        "match",
        {"matches": [{"req_id": "R1", "match_score": 0.8}]},
    )

    assert payload["state"]["matches"][0]["req_id"] == "R1"
    saved = json.loads(
        (job_root / "nodes" / "match" / "approved" / "state.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved == {"matches": [{"req_id": "R1", "match_score": 0.8}]}


def test_editor_state_rejects_unknown_node(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "jobs"
    monkeypatch.setenv("PHD2_DATA_ROOT", str(data_root))
    (data_root / "tu_berlin" / "201003").mkdir(parents=True, exist_ok=True)

    try:
        editor_state("tu_berlin", "201003", "unknown")
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "status_code", None) == 404
    else:
        raise AssertionError("expected HTTPException for unsupported node")


def test_stage_outputs_reads_generate_documents_files(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "jobs"
    monkeypatch.setenv("PHD2_DATA_ROOT", str(data_root))
    job_root = data_root / "tu_berlin" / "201004"
    _write_json(
        job_root / "nodes" / "generate_documents" / "approved" / "state.json",
        {"ok": True},
    )
    (job_root / "nodes" / "generate_documents" / "proposed").mkdir(
        parents=True, exist_ok=True
    )
    (job_root / "nodes" / "generate_documents" / "proposed" / "cv.md").write_text(
        "cv content", encoding="utf-8"
    )

    payload = stage_outputs("tu_berlin", "201004", "generate_documents")

    assert payload["stage"] == "generate_documents"
    assert any(file["path"].endswith("cv.md") for file in payload["files"])


def test_document_payload_reads_and_writes(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "jobs"
    monkeypatch.setenv("PHD2_DATA_ROOT", str(data_root))
    job_root = data_root / "tu_berlin" / "201005"
    job_root.mkdir(parents=True, exist_ok=True)

    payload = update_document_payload(
        "tu_berlin",
        "201005",
        "cv",
        {"content": "updated cv markdown"},
    )

    assert payload["content"] == "updated cv markdown"
    loaded = document_payload("tu_berlin", "201005", "cv")
    assert loaded["content"] == "updated cv markdown"
