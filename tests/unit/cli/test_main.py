"""Tests for unified CLI parsing and batch helpers."""

from __future__ import annotations

import asyncio
from argparse import Namespace
import json

from src.cli.main import _build_parser, _newest_jobs_for_sources
import src.cli.main as cli_main
from src.core.api_client import LangGraphAPIClient
from src.core.data_manager import DataManager


def test_review_parser_supports_explorer_mode() -> None:
    parser = _build_parser()

    args = parser.parse_args(["review"])

    assert args.command == "review"
    assert args.source is None
    assert args.job_id is None


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


def test_run_pipeline_returns_nonzero_on_failed_remote_run(monkeypatch) -> None:
    class _FakeThreadAPI:
        async def get_state(self, thread_id):
            return {"next": []}

    class _FakeSDKClient:
        threads = _FakeThreadAPI()

    class _FakeAPIClient:
        @staticmethod
        def ensure_server():
            return "http://test"

        def __init__(self, url):
            self.url = url
            self.client = _FakeSDKClient()

        @staticmethod
        def thread_id_for(source, job_id):
            return f"{source}:{job_id}"

        async def invoke_assistant(self, *args, **kwargs):
            return {"status": "failed", "error": "403 PERMISSION_DENIED"}

    monkeypatch.setattr(cli_main, "LangGraphAPIClient", _FakeAPIClient)
    monkeypatch.setattr(cli_main, "_translate_jobs", lambda jobs: jobs)

    args = Namespace(
        source="xing",
        job_id="123",
        source_url=None,
        profile_evidence=None,
        requirements=None,
        auto_approve_review=False,
    )

    assert asyncio.run(cli_main._run_pipeline(args)) == 1


def test_run_review_returns_nonzero_when_api_is_unhealthy(monkeypatch) -> None:
    class _FakeAPIClient:
        def __init__(self):
            self.url = "http://test"

        def is_healthy(self):
            return False

    monkeypatch.setattr(cli_main, "LangGraphAPIClient", _FakeAPIClient)

    args = Namespace(source="xing", job_id="123")

    assert cli_main._run_review(args) == 1


def test_run_generate_uses_current_pipeline_signature(monkeypatch, capsys) -> None:
    def fake_generate_application_documents(**kwargs):
        assert kwargs == {
            "source": "xing",
            "job_id": "123",
            "profile_path": cli_main.DEFAULT_PROFILE_PATH,
            "target_language": "en",
        }
        return {"status": "assembled"}

    monkeypatch.setattr(
        "src.core.ai.generate_documents_v2.generate_application_documents",
        fake_generate_application_documents,
    )

    args = Namespace(
        source="xing",
        job_id="123",
        profile=None,
        language="en",
        render=False,
        engine="tex",
    )

    assert cli_main._run_generate(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"status": "assembled", "render_outputs": {}}


def test_run_generate_renders_cv_and_letter_when_requested(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "src.core.ai.generate_documents_v2.generate_application_documents",
        lambda **kwargs: {"status": "assembled"},
    )

    calls: list[list[str]] = []

    def fake_render_main(argv):
        calls.append(argv)
        return 0

    monkeypatch.setattr("src.core.tools.render.main.main", fake_render_main)

    args = Namespace(
        source="xing",
        job_id="123",
        profile=None,
        language="en",
        render=True,
        engine="docx",
    )

    assert cli_main._run_generate(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["render_outputs"] == {"cv": 0, "letter": 0}
    assert calls == [
        [
            "cv",
            "--source",
            "xing",
            "--job-id",
            "123",
            "--engine",
            "docx",
            "--language",
            "en",
        ],
        [
            "letter",
            "--source",
            "xing",
            "--job-id",
            "123",
            "--engine",
            "docx",
            "--language",
            "en",
        ],
    ]
