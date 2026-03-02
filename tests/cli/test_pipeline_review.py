from src.cli import pipeline
from src.cli.pipeline import (
    build_archive_passed_plan,
    build_jobs_inventory,
    build_jobs_index,
    collect_prep_comments,
    parse_deadline_date,
    parse_state_entries,
    write_review_comments,
)


def test_collect_prep_comments_reads_html_comments(tmp_path):
    prep_dir = tmp_path / "prep"
    prep_dir.mkdir(parents=True, exist_ok=True)
    (prep_dir / "a.md").write_text(
        "Line\n<!-- first comment -->\nMore\n<!-- second -->\n", encoding="utf-8"
    )

    comments = collect_prep_comments(prep_dir)
    assert len(comments) == 2
    assert comments[0]["file"] == "a.md"
    assert comments[0]["comment"] == "first comment"


def test_collect_prep_comments_ignores_prep_readme(tmp_path):
    prep_dir = tmp_path / "prep"
    prep_dir.mkdir(parents=True, exist_ok=True)
    (prep_dir / "README.md").write_text(
        "Example <!-- this should be ignored -->", encoding="utf-8"
    )

    comments = collect_prep_comments(prep_dir)
    assert comments == []


def test_write_review_comments_reports_zero(tmp_path):
    review_dir = tmp_path / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    report = write_review_comments(review_dir, [])

    text = report.read_text(encoding="utf-8")
    assert "No unresolved HTML comments found" in text


def test_collect_prep_comments_filters_by_target(tmp_path):
    prep_dir = tmp_path / "prep"
    (prep_dir / "cv").mkdir(parents=True, exist_ok=True)
    (prep_dir / "motivation").mkdir(parents=True, exist_ok=True)
    (prep_dir / "cv" / "cv.to_render.md").write_text(
        "<!-- cv comment -->", encoding="utf-8"
    )
    (prep_dir / "motivation" / "motivation.pre.md").write_text(
        "<!-- motivation comment -->", encoding="utf-8"
    )

    cv_comments = collect_prep_comments(prep_dir, target="cv")
    motivation_comments = collect_prep_comments(prep_dir, target="motivation")

    assert len(cv_comments) == 1
    assert cv_comments[0]["comment"] == "cv comment"
    assert len(motivation_comments) == 1
    assert motivation_comments[0]["comment"] == "motivation comment"


def test_parse_state_entries_reads_latest_state(tmp_path):
    state = tmp_path / "state.md"
    state.write_text(
        "\n".join(
            [
                "# Application Pipeline State",
                "",
                "## 2026-03-01T00:00:00+00:00 | stage=prepare | target=all | status=ready_for_review",
                "## 2026-03-01T00:01:00+00:00 | stage=review | target=all | status=ready_to_renderize",
            ]
        ),
        encoding="utf-8",
    )

    entries = parse_state_entries(state)
    assert len(entries) == 2
    assert entries[-1]["stage"] == "review"
    assert entries[-1]["status"] == "ready_to_renderize"


def test_build_jobs_index_groups_ids_by_source(tmp_path, monkeypatch):
    root = tmp_path / "data" / "pipelined_data"
    (root / "tu_berlin" / "201084").mkdir(parents=True, exist_ok=True)
    (root / "tu_berlin" / "201115").mkdir(parents=True, exist_ok=True)
    (root / "eth" / "300001").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path)
    index = build_jobs_index(source="all")

    assert sorted(index["tu_berlin"]) == ["201084", "201115"]
    assert index["eth"] == ["300001"]


def test_build_jobs_inventory_includes_archive_and_overlap(tmp_path, monkeypatch):
    root = tmp_path / "data" / "pipelined_data"
    (root / "tu_berlin" / "201084").mkdir(parents=True, exist_ok=True)
    (root / "tu_berlin" / "201115").mkdir(parents=True, exist_ok=True)
    (root / "tu_berlin" / "archive" / "201115").mkdir(parents=True, exist_ok=True)
    (root / "tu_berlin" / "archive" / "200001").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path)
    inventory = build_jobs_inventory(source="all")

    assert inventory["tu_berlin"]["active"] == ["201084", "201115"]
    assert inventory["tu_berlin"]["archive"] == ["200001", "201115"]
    assert inventory["tu_berlin"]["duplicates"] == ["201115"]
    assert inventory["tu_berlin"]["unique_known"] == ["200001", "201084", "201115"]


def test_parse_deadline_date_supports_dot_and_iso_formats():
    dot_date = parse_deadline_date("20.03.2026")
    iso_date = parse_deadline_date("2026-03-20")
    assert dot_date is not None
    assert iso_date is not None
    assert dot_date.isoformat() == "2026-03-20"
    assert iso_date.isoformat() == "2026-03-20"
    assert parse_deadline_date("Unknown") is None


def test_build_archive_passed_plan_categorizes_jobs(tmp_path, monkeypatch):
    source_root = tmp_path / "data" / "pipelined_data" / "tu_berlin"
    archive_root = source_root / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)

    expired = source_root / "100001"
    expired.mkdir(parents=True, exist_ok=True)
    (expired / "job.md").write_text(
        "---\ndeadline: 01.01.2026\n---\n", encoding="utf-8"
    )

    future = source_root / "100002"
    future.mkdir(parents=True, exist_ok=True)
    (future / "job.md").write_text("---\ndeadline: 31.12.2026\n---\n", encoding="utf-8")

    missing = source_root / "100003"
    missing.mkdir(parents=True, exist_ok=True)
    (missing / "job.md").write_text("---\nstatus: Open\n---\n", encoding="utf-8")

    unparsable = source_root / "100004"
    unparsable.mkdir(parents=True, exist_ok=True)
    (unparsable / "job.md").write_text("---\ndeadline: soon\n---\n", encoding="utf-8")

    duplicated = source_root / "100005"
    duplicated.mkdir(parents=True, exist_ok=True)
    (duplicated / "job.md").write_text(
        "---\ndeadline: 15.01.2026\n---\n", encoding="utf-8"
    )
    (archive_root / "100005").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(pipeline, "REPO_ROOT", tmp_path)
    reference_date = parse_deadline_date("2026-03-02")
    assert reference_date is not None
    plan = build_archive_passed_plan(source="tu_berlin", reference_date=reference_date)

    assert plan["reference_date"] == "2026-03-02"
    assert [item["job_id"] for item in plan["eligible"]] == ["100001"]
    assert [item["job_id"] for item in plan["still_open"]] == ["100002"]
    assert plan["missing_deadline"] == ["100003"]
    assert [item["job_id"] for item in plan["unparsable_deadline"]] == ["100004"]
    assert [item["job_id"] for item in plan["already_in_archive"]] == ["100005"]
