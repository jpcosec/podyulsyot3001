from __future__ import annotations

import json
import os
from pathlib import Path

from src.nodes.render.logic import run_logic


def test_run_logic_copies_generate_documents_outputs(tmp_path: Path) -> None:
    source = "tu_berlin"
    job_id = "job-1"
    base = (
        tmp_path
        / "data/jobs"
        / source
        / job_id
        / "nodes"
        / "generate_documents"
        / "proposed"
    )
    base.mkdir(parents=True, exist_ok=True)

    (base / "cv.md").write_text("CV", encoding="utf-8")
    (base / "motivation_letter.md").write_text("LETTER", encoding="utf-8")
    (base / "application_email.md").write_text("EMAIL", encoding="utf-8")

    state = {
        "source": source,
        "job_id": job_id,
        "run_id": "run-1",
        "current_node": "generate_documents",
        "status": "running",
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        out = run_logic(state)
    finally:
        os.chdir(prev_cwd)

    assert out["current_node"] == "render"
    assert out["status"] == "running"

    render_base = tmp_path / "data/jobs" / source / job_id / "nodes" / "render"
    assert (render_base / "proposed" / "cv.md").read_text(encoding="utf-8") == "CV"
    assert (render_base / "proposed" / "motivation_letter.md").read_text(
        encoding="utf-8"
    ) == "LETTER"
    assert (render_base / "proposed" / "application_email.md").read_text(
        encoding="utf-8"
    ) == "EMAIL"

    approved = json.loads((render_base / "approved" / "state.json").read_text("utf-8"))
    assert approved["node"] == "render"
    assert set(approved["documents"]) == {
        "cv",
        "motivation_letter",
        "application_email",
    }

    execution_meta = json.loads(
        (render_base / "meta" / "execution.json").read_text(encoding="utf-8")
    )
    assert execution_meta["node"] == "render"
    assert execution_meta["current_node"] == "render"
