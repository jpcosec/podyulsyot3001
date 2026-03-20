from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.core.io import ProvenanceService
from src.nodes.package.logic import run_logic


def test_run_logic_packages_render_outputs(tmp_path: Path) -> None:
    source = "tu_berlin"
    job_id = "job-1"
    render_base = tmp_path / "data/jobs" / source / job_id / "nodes" / "render"
    proposed = render_base / "proposed"
    proposed.mkdir(parents=True, exist_ok=True)

    (proposed / "cv.md").write_text("CV", encoding="utf-8")
    (proposed / "motivation_letter.md").write_text("LETTER", encoding="utf-8")
    (proposed / "application_email.md").write_text("EMAIL", encoding="utf-8")
    (render_base / "approved").mkdir(parents=True, exist_ok=True)
    approved_payload = {
        "node": "render",
        "source": source,
        "job_id": job_id,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "documents": {
            "cv": {
                "source_ref": "nodes/generate_documents/proposed/cv.md",
                "rendered_ref": "nodes/render/proposed/cv.md",
                "sha256": ProvenanceService.sha256_text("CV"),
            },
            "motivation_letter": {
                "source_ref": "nodes/generate_documents/proposed/motivation_letter.md",
                "rendered_ref": "nodes/render/proposed/motivation_letter.md",
                "sha256": ProvenanceService.sha256_text("LETTER"),
            },
            "application_email": {
                "source_ref": "nodes/generate_documents/proposed/application_email.md",
                "rendered_ref": "nodes/render/proposed/application_email.md",
                "sha256": ProvenanceService.sha256_text("EMAIL"),
            },
        },
    }
    (render_base / "approved" / "state.json").write_text(
        json.dumps(approved_payload),
        encoding="utf-8",
    )

    state = {
        "source": source,
        "job_id": job_id,
        "run_id": "run-1",
        "current_node": "render",
        "status": "running",
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_logic(state)
    finally:
        os.chdir(prev_cwd)

    assert out["current_node"] == "package"
    assert out["status"] == "completed"

    job_root = tmp_path / "data/jobs" / source / job_id
    manifest = json.loads((job_root / "final" / "manifest.json").read_text("utf-8"))
    assert manifest["node"] == "package"
    assert set(manifest["artifacts"]) == {
        "cv",
        "motivation_letter",
        "application_email",
    }

    package_state = json.loads(
        (job_root / "nodes" / "package" / "approved" / "state.json").read_text("utf-8")
    )
    assert package_state["artifact_count"] == 3

    execution_meta = json.loads(
        (job_root / "nodes" / "package" / "meta" / "execution.json").read_text(
            encoding="utf-8"
        )
    )
    assert execution_meta["node"] == "package"
    assert execution_meta["status"] == "completed"


def test_run_logic_rejects_malformed_render_approved_state(tmp_path: Path) -> None:
    source = "tu_berlin"
    job_id = "job-2"
    render_base = tmp_path / "data/jobs" / source / job_id / "nodes" / "render"
    (render_base / "approved").mkdir(parents=True, exist_ok=True)
    (render_base / "approved" / "state.json").write_text(
        json.dumps({"node": "render"}),
        encoding="utf-8",
    )

    state = {
        "source": source,
        "job_id": job_id,
        "run_id": "run-2",
        "current_node": "render",
        "status": "running",
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        with pytest.raises(ValueError):
            run_logic(state)
    finally:
        os.chdir(prev_cwd)


def test_run_logic_rejects_hash_drift_between_approved_and_rendered_files(
    tmp_path: Path,
) -> None:
    source = "tu_berlin"
    job_id = "job-3"
    render_base = tmp_path / "data/jobs" / source / job_id / "nodes" / "render"
    proposed = render_base / "proposed"
    proposed.mkdir(parents=True, exist_ok=True)

    (proposed / "cv.md").write_text("CV drifted", encoding="utf-8")
    (proposed / "motivation_letter.md").write_text("LETTER", encoding="utf-8")
    (proposed / "application_email.md").write_text("EMAIL", encoding="utf-8")
    (render_base / "approved").mkdir(parents=True, exist_ok=True)
    approved_payload = {
        "node": "render",
        "source": source,
        "job_id": job_id,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "documents": {
            "cv": {
                "source_ref": "nodes/generate_documents/proposed/cv.md",
                "rendered_ref": "nodes/render/proposed/cv.md",
                "sha256": ProvenanceService.sha256_text("CV expected"),
            },
            "motivation_letter": {
                "source_ref": "nodes/generate_documents/proposed/motivation_letter.md",
                "rendered_ref": "nodes/render/proposed/motivation_letter.md",
                "sha256": ProvenanceService.sha256_text("LETTER"),
            },
            "application_email": {
                "source_ref": "nodes/generate_documents/proposed/application_email.md",
                "rendered_ref": "nodes/render/proposed/application_email.md",
                "sha256": ProvenanceService.sha256_text("EMAIL"),
            },
        },
    }
    (render_base / "approved" / "state.json").write_text(
        json.dumps(approved_payload),
        encoding="utf-8",
    )

    state = {
        "source": source,
        "job_id": job_id,
        "run_id": "run-3",
        "current_node": "render",
        "status": "running",
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        with pytest.raises(ValueError, match="hash mismatch"):
            run_logic(state)
    finally:
        os.chdir(prev_cwd)
