"""End-to-end style coverage for the CLI apply workflow."""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.automation.main import main
from src.automation.ariadne.danger_contracts import ApplyDangerReport
from src.automation.ariadne.session import UnsupportedRoutingDecisionError
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


def _write_ingest_state(
    jobs_root: Path,
    source: str,
    job_id: str,
    *,
    state: dict[str, object] | None = None,
) -> DataManager:
    data_manager = DataManager(jobs_root)
    data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="ingest",
        stage="proposed",
        filename="state.json",
        data=state
        or {
            "job_title": "Automation Engineer",
            "company_name": "Acme",
            "application_url": "https://www.xing.com/jobs/apply/123",
            "url": "https://www.xing.com/jobs/view/123",
        },
    )
    return data_manager


def _state_observation(**present: bool) -> dict[str, bool]:
    return {selector: present.get(selector, False) for selector in XING_SELECTORS}


@dataclass
class _ApplyRunResult:
    meta: dict[str, object]
    session_ids: list[str]
    executed_steps: list[str]
    events: list[tuple[str, str]]
    first_step_flags: list[bool]
    urls: list[str]
    step_contexts: list[dict[str, object]]


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

    async def inspect_danger(self, application_url: str | None) -> ApplyDangerReport:
        self.events.append(("inspect_danger", application_url or ""))
        return ApplyDangerReport()

    async def begin_human_intervention(self, artifact_dir: Path, step, reason: str):
        return {}


class _RecordingMotorProvider:
    def __init__(self, session: _RecordingMotorSession) -> None:
        self.session = session
        self.session_ids: list[str] = []

    @asynccontextmanager
    async def open_session(self, session_id: str, credentials=None, visible: bool = False):
        self.session_ids.append(session_id)
        yield self.session


def _install_backend(monkeypatch: pytest.MonkeyPatch, backend: str, provider) -> None:
    module_path, class_name = BACKEND_IMPORTS[backend]
    monkeypatch.setitem(
        sys.modules,
        module_path,
        SimpleNamespace(**{class_name: lambda: provider}),
    )


def _normalize_apply_meta(meta: dict[str, object]) -> dict[str, object]:
    normalized = dict(meta)
    timestamp = normalized.get("timestamp")
    assert isinstance(timestamp, str)
    datetime.fromisoformat(timestamp)
    normalized["timestamp"] = "<iso-timestamp>"
    return normalized


def _normalize_step_contexts(
    step_contexts: list[dict[str, object]],
) -> list[dict[str, object]]:
    normalized_contexts: list[dict[str, object]] = []
    for context in step_contexts:
        normalized = dict(context)
        if normalized.get("cv_path"):
            normalized["cv_path"] = "<cv-path>"
        if normalized.get("letter_path"):
            normalized["letter_path"] = "<letter-path>"
        normalized_contexts.append(normalized)
    return normalized_contexts


async def _run_apply_flow(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
    source: str = "xing",
    job_id: str,
    observations: list[dict[str, bool]],
    profile_payload: dict[str, str] | None = None,
    dry_run: bool = False,
    state: dict[str, object] | None = None,
) -> _ApplyRunResult:
    jobs_root = tmp_path / backend / "jobs"
    data_manager = _write_ingest_state(
        jobs_root, source=source, job_id=job_id, state=state
    )
    storage = AutomationStorage(data_manager)
    cv_path = tmp_path / backend / f"{job_id}-cv.pdf"
    cv_path.parent.mkdir(parents=True, exist_ok=True)
    cv_path.write_bytes(b"cv")
    argv = [
        "apply",
        "--backend",
        backend,
        "--source",
        source,
        "--job-id",
        job_id,
        "--cv",
        str(cv_path),
    ]
    if dry_run:
        argv.append("--dry-run")
    if profile_payload is not None:
        profile_path = tmp_path / backend / f"{job_id}-profile.json"
        profile_path.write_text(json.dumps(profile_payload), encoding="utf-8")
        argv.extend(["--profile-json", str(profile_path)])

    session = _RecordingMotorSession(observations=observations)
    provider = _RecordingMotorProvider(session)

    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: storage)
    _install_backend(monkeypatch, backend, provider)

    await main(argv)

    meta = data_manager.read_json_artifact(
        source=source,
        job_id=job_id,
        node_name="apply",
        stage="meta",
        filename="apply_meta.json",
    )
    return _ApplyRunResult(
        meta=meta,
        session_ids=provider.session_ids,
        executed_steps=session.executed_steps,
        events=session.events,
        first_step_flags=session.first_step_flags,
        urls=session.urls,
        step_contexts=session.step_contexts,
    )


@pytest.mark.asyncio
async def test_apply_cli_keeps_apply_meta_and_side_effects_consistent_across_motors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observations = [
        _state_observation(**{"[data-testid='apply-button']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='application-success']": True}),
    ]
    browseros_run = await _run_apply_flow(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        backend="browseros",
        job_id="job-123-browseros",
        observations=observations,
        profile_payload={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
        },
    )
    crawl4ai_run = await _run_apply_flow(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        backend="crawl4ai",
        job_id="job-123-crawl4ai",
        observations=observations,
        profile_payload={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
        },
    )

    assert (
        _normalize_apply_meta(browseros_run.meta)
        == _normalize_apply_meta(crawl4ai_run.meta)
        == {
            "status": "submitted",
            "timestamp": "<iso-timestamp>",
            "error": None,
        }
    )
    assert (
        browseros_run.executed_steps
        == crawl4ai_run.executed_steps
        == [
            "open_modal",
            "fill_contact",
            "upload_cv",
            "submit",
        ]
    )
    assert (
        browseros_run.events
        == crawl4ai_run.events
        == [
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "open_modal"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "fill_contact"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "upload_cv"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "submit"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
        ]
    )
    assert (
        browseros_run.first_step_flags
        == crawl4ai_run.first_step_flags
        == [
            True,
            False,
            False,
            False,
        ]
    )
    assert (
        browseros_run.urls
        == crawl4ai_run.urls
        == ["https://www.xing.com/jobs/apply/123"] * 4
    )
    assert browseros_run.session_ids == ["apply_xing_job-123-browseros"]
    assert crawl4ai_run.session_ids == ["apply_xing_job-123-crawl4ai"]
    assert _normalize_step_contexts(
        browseros_run.step_contexts
    ) == _normalize_step_contexts(crawl4ai_run.step_contexts)
    assert browseros_run.step_contexts[0]["profile"]["first_name"] == "Ada"
    assert browseros_run.step_contexts[0]["profile"]["last_name"] == "Lovelace"
    assert browseros_run.step_contexts[0]["job"]["job_title"] == "Automation Engineer"


@pytest.mark.asyncio
async def test_apply_cli_dry_run_keeps_apply_meta_and_side_effects_consistent_across_motors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observations = [
        _state_observation(**{"[data-testid='apply-button']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
        _state_observation(**{"[data-testid='apply-modal']": True}),
    ]
    browseros_run = await _run_apply_flow(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        backend="browseros",
        job_id="job-dry-run-browseros",
        observations=observations,
        dry_run=True,
    )
    crawl4ai_run = await _run_apply_flow(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        backend="crawl4ai",
        job_id="job-dry-run-crawl4ai",
        observations=observations,
        dry_run=True,
    )

    assert (
        _normalize_apply_meta(browseros_run.meta)
        == _normalize_apply_meta(crawl4ai_run.meta)
        == {
            "status": "dry_run",
            "timestamp": "<iso-timestamp>",
            "error": None,
        }
    )
    assert (
        browseros_run.executed_steps
        == crawl4ai_run.executed_steps
        == [
            "open_modal",
            "fill_contact",
            "upload_cv",
        ]
    )
    assert "submit" not in browseros_run.executed_steps
    assert "submit" not in crawl4ai_run.executed_steps
    assert (
        browseros_run.events
        == crawl4ai_run.events
        == [
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "open_modal"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "fill_contact"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
            ("execute", "upload_cv"),
            ("inspect_danger", "https://www.xing.com/jobs/apply/123"),
            ("observe", ",".join(XING_SELECTORS)),
        ]
    )
    assert (
        browseros_run.first_step_flags
        == crawl4ai_run.first_step_flags
        == [
            True,
            False,
            False,
        ]
    )
    assert (
        browseros_run.urls
        == crawl4ai_run.urls
        == ["https://www.xing.com/jobs/apply/123"] * 3
    )


@pytest.mark.asyncio
async def test_apply_cli_persists_failure_when_portal_routing_requires_external_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs_root = tmp_path / "browseros" / "jobs"
    data_manager = _write_ingest_state(
        jobs_root,
        source="linkedin",
        job_id="job-external-linkedin",
        state={
            "job_title": "Automation Engineer",
            "company_name": "Acme",
            "application_method": "direct_url",
            "application_url": "https://company.example.test/greenhouse/apply/123",
            "url": "https://www.linkedin.com/jobs/view/123",
        },
    )
    storage = AutomationStorage(data_manager)
    cv_path = tmp_path / "browseros" / "linkedin-cv.pdf"
    cv_path.parent.mkdir(parents=True, exist_ok=True)
    cv_path.write_bytes(b"cv")

    provider = _RecordingMotorProvider(_RecordingMotorSession(observations=[]))
    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: storage)
    _install_backend(monkeypatch, "browseros", provider)

    with pytest.raises(
        UnsupportedRoutingDecisionError, match="external_application_route"
    ):
        await main(
            [
                "apply",
                "--backend",
                "browseros",
                "--source",
                "linkedin",
                "--job-id",
                "job-external-linkedin",
                "--cv",
                str(cv_path),
            ]
        )

    meta = data_manager.read_json_artifact(
        source="linkedin",
        job_id="job-external-linkedin",
        node_name="apply",
        stage="meta",
        filename="apply_meta.json",
    )
    assert meta["status"] == "failed"
    assert "external_application_route" in meta["error"]
    assert provider.session_ids == []


@pytest.mark.asyncio
async def test_apply_cli_persists_failure_when_portal_routing_requires_email_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs_root = tmp_path / "browseros" / "jobs"
    data_manager = _write_ingest_state(
        jobs_root,
        source="stepstone",
        job_id="job-email-stepstone",
        state={
            "job_title": "Data Engineer",
            "company_name": "Acme GmbH",
            "application_method": "Apply by email",
            "application_email": "mailto:karriere@acme.de?subject=Bewerbung",
            "url": "https://www.stepstone.de/stellenangebote--data-engineer-xyz",
        },
    )
    storage = AutomationStorage(data_manager)
    cv_path = tmp_path / "browseros" / "stepstone-cv.pdf"
    cv_path.parent.mkdir(parents=True, exist_ok=True)
    cv_path.write_bytes(b"cv")

    provider = _RecordingMotorProvider(_RecordingMotorSession(observations=[]))
    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: storage)
    _install_backend(monkeypatch, "browseros", provider)

    with pytest.raises(
        UnsupportedRoutingDecisionError, match="email_application_route"
    ):
        await main(
            [
                "apply",
                "--backend",
                "browseros",
                "--source",
                "stepstone",
                "--job-id",
                "job-email-stepstone",
                "--cv",
                str(cv_path),
            ]
        )

    meta = data_manager.read_json_artifact(
        source="stepstone",
        job_id="job-email-stepstone",
        node_name="apply",
        stage="meta",
        filename="apply_meta.json",
    )
    assert meta["status"] == "failed"
    assert "email_application_route" in meta["error"]
    assert provider.session_ids == []


@pytest.mark.asyncio
async def test_apply_cli_persists_failure_when_portal_routing_is_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jobs_root = tmp_path / "crawl4ai" / "jobs"
    data_manager = _write_ingest_state(
        jobs_root,
        source="xing",
        job_id="job-unsupported-xing",
        state={
            "job_title": "Data Engineer",
            "company_name": "Acme",
        },
    )
    storage = AutomationStorage(data_manager)
    cv_path = tmp_path / "crawl4ai" / "xing-cv.pdf"
    cv_path.parent.mkdir(parents=True, exist_ok=True)
    cv_path.write_bytes(b"cv")

    provider = _RecordingMotorProvider(_RecordingMotorSession(observations=[]))
    monkeypatch.setattr("src.automation.main._setup_logging", lambda name: None)
    monkeypatch.setattr("src.automation.main.AutomationStorage", lambda: storage)
    _install_backend(monkeypatch, "crawl4ai", provider)

    with pytest.raises(
        UnsupportedRoutingDecisionError, match="unsupported_application_route"
    ):
        await main(
            [
                "apply",
                "--backend",
                "crawl4ai",
                "--source",
                "xing",
                "--job-id",
                "job-unsupported-xing",
                "--cv",
                str(cv_path),
            ]
        )

    meta = data_manager.read_json_artifact(
        source="xing",
        job_id="job-unsupported-xing",
        node_name="apply",
        stage="meta",
        filename="apply_meta.json",
    )
    assert meta["status"] == "failed"
    assert "unsupported_application_route" in meta["error"]
    assert provider.session_ids == []
