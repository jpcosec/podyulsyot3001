"""End-to-end style coverage for the CLI apply workflow."""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.automation.main import main
from src.automation.storage import AutomationStorage
from src.core.data_manager import DataManager

XING_SELECTORS = (
    "[data-testid='application-success']",
    "[data-testid='apply-button']",
    "[data-testid='apply-modal']",
)

BACKEND_IMPORTS = {
    "browseros": (
        "src.automation.motors.browseros.cli.backend",
        "BrowserOSMotorProvider",
    ),
    "crawl4ai": (
        "src.automation.motors.crawl4ai.apply_engine",
        "C4AIMotorProvider",
    ),
}


def _write_ingest_state(jobs_root: Path, source: str, job_id: str) -> DataManager:
    data_manager = DataManager(jobs_root)
    data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="ingest",
        stage="proposed",
        filename="state.json",
        data={
            "job_title": "Automation Engineer",
            "company_name": "Acme",
            "application_url": "https://example.com/jobs/apply/123",
        },
    )
    return data_manager


def _state_observation(**present: bool) -> dict[str, bool]:
    return {selector: present.get(selector, False) for selector in XING_SELECTORS}


class _RecordingMotorSession:
    def __init__(self, observations: list[dict[str, bool]]) -> None:
        self._observations = list(observations)
        self.events: list[tuple[str, str]] = []
        self.executed_steps: list[str] = []
        self.step_contexts: list[dict[str, object]] = []
        self.urls: list[str] = []
        self.first_step_flags: list[bool] = []

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        self.events.append(("observe", ",".join(sorted(selectors))))
        if not self._observations:
            raise AssertionError("No observation left for apply flow")
        observation = self._observations.pop(0)
        return {selector: observation.get(selector, False) for selector in selectors}

    async def execute_step(
        self,
        step,
        context,
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str,
    ) -> None:
        self.events.append(("execute", step.name))
        self.executed_steps.append(step.name)
        self.step_contexts.append(context)
        self.urls.append(url)
        self.first_step_flags.append(is_first)


class _RecordingMotorProvider:
    def __init__(self, session: _RecordingMotorSession) -> None:
        self.session = session
        self.session_ids: list[str] = []

    @asynccontextmanager
    async def open_session(self, session_id: str):
        self.session_ids.append(session_id)
        yield self.session


def _install_backend(monkeypatch: pytest.MonkeyPatch, backend: str, provider) -> None:
    module_path, class_name = BACKEND_IMPORTS[backend]
    monkeypatch.setitem(
        sys.modules,
        module_path,
        SimpleNamespace(**{class_name: lambda: provider}),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["browseros", "crawl4ai"])
async def test_apply_cli_persists_submitted_meta_and_step_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    jobs_root = tmp_path / "jobs"
    data_manager = _write_ingest_state(jobs_root, source="xing", job_id="job-123")
    storage = AutomationStorage(data_manager)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
            }
        ),
        encoding="utf-8",
    )
    cv_path = tmp_path / "cv.pdf"
    cv_path.write_bytes(b"cv")
    session = _RecordingMotorSession(
        observations=[
            _state_observation(**{"[data-testid='apply-button']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='application-success']": True}),
        ]
    )
    provider = _RecordingMotorProvider(session)

    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: storage)
    _install_backend(monkeypatch, backend, provider)

    await main(
        [
            "apply",
            "--backend",
            backend,
            "--source",
            "xing",
            "--job-id",
            "job-123",
            "--cv",
            str(cv_path),
            "--profile-json",
            str(profile_path),
        ]
    )

    meta = data_manager.read_json_artifact(
        source="xing",
        job_id="job-123",
        node_name="apply",
        stage="meta",
        filename="apply_meta.json",
    )

    assert meta["status"] == "submitted"
    assert provider.session_ids == ["apply_xing_job-123"]
    assert session.executed_steps == [
        "open_modal",
        "fill_contact",
        "upload_cv",
        "submit",
    ]
    assert session.events == [
        ("observe", ",".join(XING_SELECTORS)),
        ("execute", "open_modal"),
        ("observe", ",".join(XING_SELECTORS)),
        ("observe", ",".join(XING_SELECTORS)),
        ("execute", "fill_contact"),
        ("observe", ",".join(XING_SELECTORS)),
        ("observe", ",".join(XING_SELECTORS)),
        ("execute", "upload_cv"),
        ("observe", ",".join(XING_SELECTORS)),
        ("observe", ",".join(XING_SELECTORS)),
        ("execute", "submit"),
        ("observe", ",".join(XING_SELECTORS)),
    ]
    assert session.first_step_flags == [True, False, False, False]
    assert session.urls == ["https://example.com/jobs/apply/123"] * 4
    assert session.step_contexts[0]["profile"]["first_name"] == "Ada"
    assert session.step_contexts[0]["profile"]["last_name"] == "Lovelace"
    assert session.step_contexts[0]["job"]["job_title"] == "Automation Engineer"


@pytest.mark.asyncio
async def test_apply_cli_dry_run_persists_meta_before_submit_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs_root = tmp_path / "jobs"
    data_manager = _write_ingest_state(jobs_root, source="xing", job_id="job-dry-run")
    storage = AutomationStorage(data_manager)
    cv_path = tmp_path / "cv.pdf"
    cv_path.write_bytes(b"cv")
    session = _RecordingMotorSession(
        observations=[
            _state_observation(**{"[data-testid='apply-button']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
            _state_observation(**{"[data-testid='apply-modal']": True}),
        ]
    )
    provider = _RecordingMotorProvider(session)

    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: storage)
    _install_backend(monkeypatch, "browseros", provider)

    await main(
        [
            "apply",
            "--source",
            "xing",
            "--job-id",
            "job-dry-run",
            "--cv",
            str(cv_path),
            "--dry-run",
        ]
    )

    meta = data_manager.read_json_artifact(
        source="xing",
        job_id="job-dry-run",
        node_name="apply",
        stage="meta",
        filename="apply_meta.json",
    )

    assert meta["status"] == "dry_run"
    assert session.executed_steps == ["open_modal", "fill_contact", "upload_cv"]
    assert "submit" not in session.executed_steps
