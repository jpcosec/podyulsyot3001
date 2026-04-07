"""Verify that MotorSession and MotorProvider are structural (Protocol) types."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import pytest

from src.automation.ariadne.danger_contracts import ApplyDangerReport
from src.automation.ariadne.motor_protocol import MotorProvider, MotorSession


class _FakeSession:
    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        return {s: False for s in selectors}

    async def execute_step(self, step, context, cv_path, letter_path, is_first, url):
        pass

    async def inspect_danger(self, application_url: str | None) -> ApplyDangerReport:
        return ApplyDangerReport()

    async def begin_human_intervention(self, artifact_dir: Path, step, reason: str):
        return {}


class _FakeProvider:
    @asynccontextmanager
    async def open_session(
        self, session_id: str, credentials=None
    ) -> AsyncIterator[_FakeSession]:
        yield _FakeSession()


def test_fake_session_satisfies_protocol():
    s: MotorSession = _FakeSession()  # type: ignore[assignment]
    assert callable(s.observe)
    assert callable(s.execute_step)


def test_fake_provider_satisfies_protocol():
    p: MotorProvider = _FakeProvider()  # type: ignore[assignment]
    assert callable(p.open_session)


@pytest.mark.asyncio
async def test_provider_yields_session():
    provider = _FakeProvider()
    async with provider.open_session("test-id") as session:
        result = await session.observe({"div.foo"})
        assert result == {"div.foo": False}


def test_isinstance_checks_are_structural():
    assert isinstance(_FakeSession(), MotorSession)
    assert isinstance(_FakeProvider(), MotorProvider)


def test_non_conforming_class_fails_isinstance():
    class _Empty:
        pass

    assert not isinstance(_Empty(), MotorSession)
    assert not isinstance(_Empty(), MotorProvider)
