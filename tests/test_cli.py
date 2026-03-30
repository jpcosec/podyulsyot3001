"""Tests for unified CLI parsing and batch helpers."""

from __future__ import annotations

from src.cli.main import _build_parser, _newest_jobs_for_sources
from src.core.api_client import LangGraphAPIClient
from src.core.data_manager import DataManager


def test_review_parser_supports_explorer_mode() -> None:
    parser = _build_parser()

    args = parser.parse_args(["review"])

    assert args.command == "review"
    assert args.source is None
    assert args.job_id is None


def test_search_parser_accepts_multiple_sources() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "search",
            "--sources",
            "xing",
            "stepstone",
            "--job-query",
            "data scientist",
            "--city",
            "berlin",
        ]
    )

    assert args.sources == ["xing", "stepstone"]


def test_newest_jobs_for_sources_returns_most_recent_per_source(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    manager.ingest_raw_job(source="xing", job_id="1", payload={"job_title": "A"})
    manager.ingest_raw_job(source="xing", job_id="2", payload={"job_title": "B"})
    manager.ingest_raw_job(source="stepstone", job_id="9", payload={"job_title": "C"})

    jobs = _newest_jobs_for_sources(manager, ["xing", "stepstone"], limit=1)

    assert ("xing", "2") in jobs
    assert ("stepstone", "9") in jobs


def test_thread_id_for_is_deterministic_uuid() -> None:
    first = LangGraphAPIClient.thread_id_for("xing", "123")
    second = LangGraphAPIClient.thread_id_for("xing", "123")

    assert first == second
    assert len(first) == 36
