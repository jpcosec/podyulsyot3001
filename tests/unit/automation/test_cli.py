"""Tests for the unified automation CLI parser."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from src.automation.main import _run_apply, build_parser


def test_scrape_subcommand_requires_source():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape"])


def test_scrape_parses_source_and_defaults():
    parser = build_parser()
    args = parser.parse_args(["scrape", "--source", "stepstone"])
    assert args.command == "scrape"
    assert args.source == "stepstone"
    assert args.overwrite is False
    assert args.limit is None


def test_scrape_parses_all_options():
    parser = build_parser()
    args = parser.parse_args(
        [
            "scrape",
            "--source",
            "xing",
            "--job-query",
            "data scientist",
            "--city",
            "berlin",
            "--max-days",
            "7",
            "--limit",
            "10",
            "--overwrite",
        ]
    )
    assert args.job_query == "data scientist"
    assert args.max_days == 7
    assert args.limit == 10
    assert args.overwrite is True


def test_apply_subcommand_requires_source():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["apply"])


def test_apply_parses_apply_mode():
    parser = build_parser()
    args = parser.parse_args(
        [
            "apply",
            "--source",
            "xing",
            "--job-id",
            "12345",
            "--cv",
            "/path/cv.pdf",
            "--dry-run",
        ]
    )
    assert args.command == "apply"
    assert args.source == "xing"
    assert args.job_id == "12345"
    assert args.cv_path == "/path/cv.pdf"
    assert args.dry_run is True
    assert args.backend == "browseros"


def test_apply_parses_setup_session():
    parser = build_parser()
    args = parser.parse_args(["apply", "--source", "xing", "--setup-session"])
    assert args.setup_session is True
    assert args.job_id is None


def test_apply_parses_credential_json() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["apply", "--source", "xing", "--credential-json", "credentials.json"]
    )
    assert args.credential_json == "credentials.json"


def test_apply_parses_browseros_backend():
    parser = build_parser()
    args = parser.parse_args(
        [
            "apply",
            "--backend",
            "browseros",
            "--source",
            "linkedin",
            "--job-id",
            "99",
            "--cv",
            "/cv.pdf",
        ]
    )
    assert args.backend == "browseros"
    assert args.source == "linkedin"


@pytest.mark.asyncio
async def test_run_apply_passes_profile_json_to_session(tmp_path, monkeypatch):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps({"first_name": "Ada"}), encoding="utf-8")
    credential_path = tmp_path / "credentials.json"
    credential_path.write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "portal_name": "xing",
                        "domains": ["xing.com"],
                        "secrets": {
                            "password": {"env_var": "XING_PASSWORD", "required": True}
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    class FakeSession:
        def __init__(self, portal_name: str, storage) -> None:
            captured["portal_name"] = portal_name
            captured["storage"] = storage

        async def run(self, motor, **kwargs):
            captured["motor"] = motor
            captured["kwargs"] = kwargs
            return SimpleNamespace(status="submitted")

    fake_motor = object()

    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: object())
    monkeypatch.setitem(
        sys.modules,
        "src.automation.ariadne.session",
        SimpleNamespace(AriadneSession=FakeSession),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.automation.motors.browseros.cli.backend",
        SimpleNamespace(BrowserOSMotorProvider=lambda: fake_motor),
    )

    args = build_parser().parse_args(
        [
            "apply",
            "--source",
            "xing",
            "--job-id",
            "12345",
            "--cv",
            "/path/cv.pdf",
            "--profile-json",
            str(profile_path),
            "--credential-json",
            str(credential_path),
        ]
    )

    await _run_apply(args)

    assert captured["portal_name"] == "xing"
    assert captured["motor"] is fake_motor
    assert captured["kwargs"]["profile"] == {"first_name": "Ada"}
    assert captured["kwargs"]["credentials"]["bindings"][0]["portal_name"] == "xing"
