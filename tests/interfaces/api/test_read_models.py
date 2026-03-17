from __future__ import annotations

import json
from pathlib import Path

from src.interfaces.api.read_models import (
    build_job_timeline,
    build_view_one_payload,
    build_view_three_payload,
    build_view_two_payload,
    list_jobs,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_job_timeline_marks_pending_review(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    job_root = data_root / "tu_berlin" / "201999"

    _write_json(
        job_root / "nodes" / "scrape" / "approved" / "state.json",
        {"ok": True},
    )
    _write_json(
        job_root / "nodes" / "translate_if_needed" / "approved" / "state.json",
        {"ok": True},
    )
    _write_json(
        job_root / "nodes" / "extract_understand" / "approved" / "state.json",
        {"ok": True},
    )
    _write_json(
        job_root / "nodes" / "match" / "approved" / "state.json",
        {"ok": True},
    )
    decision_md = job_root / "nodes" / "match" / "review" / "decision.md"
    decision_md.parent.mkdir(parents=True, exist_ok=True)
    decision_md.write_text("[x] approve", encoding="utf-8")

    timeline = build_job_timeline(data_root, "tu_berlin", "201999")

    assert timeline.current_node == "review_match"
    assert timeline.status == "pending_review"
    review_stage = next(
        item for item in timeline.stages if item.stage == "review_match"
    )
    assert review_stage.status == "paused_review"


def test_list_jobs_returns_all_job_roots(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    first = data_root / "source_a" / "1001"
    second = data_root / "source_b" / "2002"

    _write_json(first / "nodes" / "scrape" / "approved" / "state.json", {"ok": True})
    _write_json(second / "nodes" / "scrape" / "approved" / "state.json", {"ok": True})

    jobs = list_jobs(data_root)
    keys = {(item.source, item.job_id) for item in jobs}
    assert keys == {("source_a", "1001"), ("source_b", "2002")}


def test_build_view_two_payload_derives_requirement_spans(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    job_root = data_root / "tu_berlin" / "201111"

    source_text = "Line one\nKnowledge of English at C1 level\nLine three"
    source_file = job_root / "raw" / "source_text.md"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(source_text, encoding="utf-8")

    _write_json(
        job_root / "nodes" / "extract_understand" / "approved" / "state.json",
        {
            "requirements": [
                {
                    "id": "R2",
                    "text": "Knowledge of English at C1 level.",
                    "priority": "must",
                }
            ]
        },
    )

    payload = build_view_two_payload(data_root, "tu_berlin", "201111")

    assert payload.requirements
    assert payload.requirements[0].id == "R2"
    assert payload.requirements[0].spans
    assert payload.requirements[0].spans[0].start_line == 2


def test_build_view_one_payload_builds_graph_edges(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    job_root = data_root / "tu_berlin" / "201112"

    _write_json(
        job_root / "nodes" / "extract_understand" / "approved" / "state.json",
        {"requirements": [{"id": "R1", "text": "Python", "priority": "must"}]},
    )
    _write_json(
        job_root / "nodes" / "match" / "approved" / "state.json",
        {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.9,
                    "evidence_id": "P_SKL_001",
                    "reasoning": "Strong evidence",
                }
            ]
        },
    )

    payload = build_view_one_payload(data_root, "tu_berlin", "201112")

    node_ids = {node.id for node in payload.nodes}
    assert "profile" in node_ids
    assert "job" in node_ids
    assert "R1" in node_ids
    assert any(
        edge.label == "MATCHED_BY" and edge.score == 0.9 for edge in payload.edges
    )


def test_build_view_three_payload_loads_documents(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    job_root = data_root / "tu_berlin" / "201113"

    _write_json(
        job_root / "nodes" / "match" / "approved" / "state.json", {"matches": []}
    )
    _write_json(
        job_root / "nodes" / "extract_understand" / "approved" / "state.json",
        {"requirements": []},
    )

    for file_name, content in {
        "cv.md": "cv content",
        "motivation_letter.md": "motivation content",
        "application_email.md": "email content",
    }.items():
        file_path = job_root / "nodes" / "generate_documents" / "proposed" / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    payload = build_view_three_payload(data_root, "tu_berlin", "201113")

    assert payload.documents["cv"] == "cv content"
    assert payload.documents["motivation_letter"] == "motivation content"
    assert payload.documents["application_email"] == "email content"
