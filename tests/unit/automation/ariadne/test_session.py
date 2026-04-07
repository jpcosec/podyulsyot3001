"""Unit tests for AriadneSession orchestrator."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.automation.ariadne.models import (
    AriadneObserve,
    AriadnePath,
    AriadnePortalMap,
    AriadneStep,
    AriadneTask,
    AriadneState,
    ApplyMeta,
)
from src.automation.ariadne.session import AriadneSession


def _minimal_map() -> AriadnePortalMap:
    """Minimal valid portal map for testing (1 state, 1 task, 1 path with 1 step)."""
    step = AriadneStep(
        step_index=1,
        name="fill_form",
        description="Fill the form",
        observe=AriadneObserve(required_elements=[]),
        actions=[],
        dry_run_stop=False,
    )
    return AriadnePortalMap(
        portal_name="test_portal",
        base_url="https://example.com",
        states={
            "success": AriadneState(
                id="success",
                description="Application sent",
                presence_predicate=AriadneObserve(required_elements=[]),
            )
        },
        tasks={
            "submit_easy_apply": AriadneTask(
                id="submit_easy_apply",
                goal="Submit",
                entry_state="job_details",
                success_states=["success"],
                failure_states=[],
            )
        },
        paths={
            "standard_easy_apply": AriadnePath(
                id="standard_easy_apply",
                task_id="submit_easy_apply",
                steps=[step],
            )
        },
    )


class _FakeSession:
    def __init__(self):
        self.observe = AsyncMock(return_value={})
        self.execute_step = AsyncMock()


class _FakeProvider:
    def __init__(self, session: _FakeSession):
        self._session = session

    @asynccontextmanager
    async def open_session(self, session_id: str) -> AsyncIterator[_FakeSession]:
        yield self._session


def _make_session(map_: AriadnePortalMap) -> tuple[AriadneSession, MagicMock]:
    storage = MagicMock()
    storage.check_already_submitted.return_value = False
    storage.get_job_state.return_value = {
        "job_title": "Dev",
        "company_name": "Acme",
        "application_url": "https://example.com/apply",
    }
    storage.write_apply_meta = MagicMock()

    sess = AriadneSession.__new__(AriadneSession)
    sess.portal_name = "test_portal"
    sess.storage = storage
    sess._map = map_
    return sess, storage


@pytest.mark.asyncio
async def test_already_submitted_raises():
    sess, storage = _make_session(_minimal_map())
    storage.check_already_submitted.return_value = True
    motor = _FakeProvider(_FakeSession())

    with pytest.raises(RuntimeError, match="already submitted"):
        await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"))


@pytest.mark.asyncio
async def test_invalid_path_id_raises():
    sess, _ = _make_session(_minimal_map())
    motor = _FakeProvider(_FakeSession())

    with pytest.raises(ValueError, match="Path 'missing' not found"):
        await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"), path_id="missing")


@pytest.mark.asyncio
async def test_run_calls_execute_step_once():
    sess, storage = _make_session(_minimal_map())
    fake_session = _FakeSession()
    motor = _FakeProvider(fake_session)

    meta = await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"))

    assert meta.status == "submitted"
    fake_session.execute_step.assert_called_once()
    storage.write_apply_meta.assert_called_once()


@pytest.mark.asyncio
async def test_dry_run_stops_before_dry_run_stop_step():
    map_ = _minimal_map()
    map_.paths["standard_easy_apply"].steps[0].dry_run_stop = True
    sess, _ = _make_session(map_)
    fake_session = _FakeSession()
    motor = _FakeProvider(fake_session)

    meta = await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"), dry_run=True)

    assert meta.status == "dry_run"
    fake_session.execute_step.assert_not_called()


@pytest.mark.asyncio
async def test_meta_written_on_failure():
    sess, storage = _make_session(_minimal_map())
    fake_session = _FakeSession()
    fake_session.execute_step.side_effect = RuntimeError("boom")
    motor = _FakeProvider(fake_session)

    with pytest.raises(RuntimeError, match="boom"):
        await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"))

    written = storage.write_apply_meta.call_args[0]
    assert written[2]["status"] == "failed"
    assert "boom" in written[2]["error"]
