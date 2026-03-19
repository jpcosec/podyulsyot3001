from __future__ import annotations

import json
from pathlib import Path

from src.interfaces.api.read_models import (
    build_cv_profile_graph_payload,
    build_base_cv_graph_payload,
    build_job_timeline,
    build_view_one_payload,
    build_view_three_payload,
    build_view_two_payload,
    list_jobs,
    load_cv_profile_graph_payload,
    save_cv_profile_graph_payload,
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


def test_build_base_cv_graph_payload_builds_deterministic_profile_graph(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "jobs"
    profile_path = (
        data_root.parent
        / "reference_data"
        / "profile"
        / "base_profile"
        / "profile_base_data.json"
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(
            {
                "snapshot_version": "1.0",
                "captured_on": "2026-02-26",
                "owner": {
                    "full_name": "Test Person",
                    "preferred_name": "Test",
                    "contact": {"email": "test@example.com"},
                    "legal_status": {
                        "visa_type": "Chancenkarte",
                        "work_permission_germany": True,
                    },
                },
                "experience": [
                    {
                        "role": "Data Engineer",
                        "organization": "ExampleOrg",
                        "achievements": ["Built ETL pipelines"],
                        "keywords": ["Python", "Airflow"],
                    }
                ],
                "education": [
                    {
                        "degree": "Electrical Engineering",
                        "institution": "Universidad de Chile",
                    }
                ],
                "publications": [
                    {
                        "title": "Paper Title",
                        "year": 2025,
                    }
                ],
                "projects": [
                    {
                        "name": "Metadata Framework",
                        "stack": ["FastAPI", "Docker"],
                    }
                ],
                "languages": [{"name": "English", "level": "CEFR C1"}],
                "skills": {
                    "programming_languages": ["Python"],
                },
            }
        ),
        encoding="utf-8",
    )

    payload = build_base_cv_graph_payload(data_root)

    node_ids = {node.id for node in payload.nodes}
    edge_ids = {edge.id for edge in payload.edges}

    assert payload.profile_id == "profile:test_person"
    assert payload.snapshot_version == "1.0"
    assert payload.captured_on == "2026-02-26"
    assert "group:experience" in node_ids
    assert "exp:0" in node_ids
    assert "exp:0:ach:0" in node_ids
    assert "skill:python" in node_ids
    assert any(edge_id.endswith(":contains") for edge_id in edge_ids)
    assert any(edge_id.endswith(":references_skill") for edge_id in edge_ids)


def test_build_cv_profile_graph_payload_uses_entry_skill_domain_model(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "jobs"
    profile_path = (
        data_root.parent
        / "reference_data"
        / "profile"
        / "base_profile"
        / "profile_base_data.json"
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(
            {
                "snapshot_version": "2.0",
                "captured_on": "2026-03-18",
                "owner": {
                    "full_name": "Jane Doe",
                    "preferred_name": "Jane",
                    "contact": {
                        "email": "jane@example.com",
                    },
                    "links": {"github": "https://github.com/jane"},
                    "legal_status": {"work_permission_germany": True},
                },
                "experience": [
                    {
                        "role": "Data Engineer",
                        "organization": "OrgX",
                        "achievements": [
                            "Built ETL pipelines in Python with Airflow",
                            "Created CI automation for data jobs",
                        ],
                        "keywords": ["Python", "Airflow"],
                    }
                ],
                "languages": [{"name": "English", "level": "C1", "note": "Daily use"}],
                "skills": {
                    "programming_languages": ["Python"],
                    "orchestration_devops": ["Airflow", "CI/CD"],
                },
            }
        ),
        encoding="utf-8",
    )

    payload = build_cv_profile_graph_payload(data_root)

    assert payload.profile_id == "profile:jane_doe"
    assert payload.snapshot_version == "2.0"
    assert payload.captured_on == "2026-03-18"

    entry_ids = {entry.id for entry in payload.entries}
    skill_ids = {skill.id for skill in payload.skills}
    edge_ids = {edge.id for edge in payload.demonstrates}

    assert any(entry.category == "job_experience" for entry in payload.entries)
    assert any(entry.category == "language_fact" for entry in payload.entries)
    assert any(entry.category == "personal_data" for entry in payload.entries)
    assert "skill:python" in skill_ids
    assert "skill:airflow" in skill_ids
    assert "skill:english" in skill_ids
    assert any(edge_id.endswith(":demonstrates:skill:python") for edge_id in edge_ids)
    assert any(edge_id.endswith(":demonstrates:skill:airflow") for edge_id in edge_ids)

    english_skill = next(
        skill for skill in payload.skills if skill.id == "skill:english"
    )
    assert english_skill.level == "C1"

    experience_entry = next(
        entry for entry in payload.entries if entry.category == "job_experience"
    )
    assert len(experience_entry.descriptions) == 2
    assert all(description.key for description in experience_entry.descriptions)
    assert all(
        description.weight == "primary_detail"
        for description in experience_entry.descriptions
    )

    assert any(
        edge.source in entry_ids and edge.target in skill_ids
        for edge in payload.demonstrates
    )


def test_save_load_cv_profile_graph_roundtrip(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    profile_path = (
        data_root.parent
        / "reference_data"
        / "profile"
        / "base_profile"
        / "profile_base_data.json"
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(
            {
                "snapshot_version": "3.0",
                "captured_on": "2026-03-18",
                "owner": {
                    "full_name": "Save Test",
                    "preferred_name": "Saver",
                    "contact": {"email": "save@test.com"},
                },
                "experience": [
                    {
                        "role": "Engineer",
                        "organization": "SaveCorp",
                        "achievements": ["Built stuff"],
                        "keywords": ["Python"],
                    }
                ],
                "skills": {"programming_languages": ["Python"]},
            }
        ),
        encoding="utf-8",
    )

    original = build_cv_profile_graph_payload(data_root)
    assert len(original.entries) > 0
    assert len(original.skills) > 0

    save_cv_profile_graph_payload(data_root, original)
    loaded = load_cv_profile_graph_payload(data_root)

    assert loaded.profile_id == original.profile_id
    assert loaded.snapshot_version == original.snapshot_version
    assert loaded.captured_on == original.captured_on
    assert len(loaded.entries) == len(original.entries)
    assert len(loaded.skills) == len(original.skills)
    assert len(loaded.demonstrates) == len(original.demonstrates)

    for orig_entry, load_entry in zip(original.entries, loaded.entries):
        assert load_entry.id == orig_entry.id
        assert load_entry.category == orig_entry.category
        assert load_entry.essential == orig_entry.essential
        assert len(load_entry.descriptions) == len(orig_entry.descriptions)

    for orig_skill, load_skill in zip(original.skills, loaded.skills):
        assert load_skill.id == orig_skill.id
        assert load_skill.label == orig_skill.label
        assert load_skill.category == orig_skill.category

    for orig_edge, load_edge in zip(original.demonstrates, loaded.demonstrates):
        assert load_edge.id == orig_edge.id
        assert load_edge.source == orig_edge.source
        assert load_edge.target == orig_edge.target
        assert load_edge.description_keys == orig_edge.description_keys


def test_save_load_prefers_saved_over_base(tmp_path: Path) -> None:
    data_root = tmp_path / "jobs"
    profile_path = (
        data_root.parent
        / "reference_data"
        / "profile"
        / "base_profile"
        / "profile_base_data.json"
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(
            {
                "snapshot_version": "1.0",
                "captured_on": "2026-01-01",
                "owner": {"full_name": "Base Person"},
                "skills": {"programming_languages": ["Java"]},
            }
        ),
        encoding="utf-8",
    )

    from src.interfaces.api.models import CvProfileGraphPayload, CvEntry, CvSkill

    custom_payload = CvProfileGraphPayload(
        profile_id="profile:edited",
        snapshot_version="99.0",
        captured_on="2099-12-31",
        entries=[
            CvEntry(
                id="entry:custom:test",
                category="custom_category",
                essential=True,
                fields={"title": "Custom Entry"},
                descriptions=[],
            )
        ],
        skills=[
            CvSkill(
                id="skill:custom",
                label="Custom Skill",
                category="custom",
                essential=True,
                level="expert",
                meta={},
            )
        ],
        demonstrates=[],
    )

    save_cv_profile_graph_payload(data_root, custom_payload)
    loaded = load_cv_profile_graph_payload(data_root)

    assert loaded.profile_id == "profile:edited"
    assert loaded.snapshot_version == "99.0"
    assert len(loaded.entries) == 1
    assert loaded.entries[0].id == "entry:custom:test"
    assert len(loaded.skills) == 1
    assert loaded.skills[0].id == "skill:custom"
