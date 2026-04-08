"""Unit tests for BrowserOSAgentMotorProvider / BrowserOSAgentMotorSession."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.automation.ariadne.models import AriadneObserve, AriadneStep
from src.automation.motors.browseros.agent.provider import (
    BrowserOSAgentMotorProvider,
    BrowserOSAgentMotorSession,
)


def test_provider_is_instantiable():
    provider = BrowserOSAgentMotorProvider()
    assert hasattr(provider, "open_session")


@pytest.mark.asyncio
async def test_open_session_returns_session():
    provider = BrowserOSAgentMotorProvider()

    async with provider.open_session("test-session") as session:
        assert isinstance(session, BrowserOSAgentMotorSession)
        assert hasattr(session, "observe")
        assert hasattr(session, "execute_step")
        assert hasattr(session, "inspect_danger")
        assert hasattr(session, "begin_human_intervention")


@pytest.mark.asyncio
async def test_observe_raises_not_implemented():
    provider = BrowserOSAgentMotorProvider()
    async with provider.open_session("sess") as session:
        with pytest.raises(NotImplementedError) as excinfo:
            await session.observe({"#any-selector"})
    assert "BrowserOS Agent motor is conceptual" in str(excinfo.value)


@pytest.mark.asyncio
async def test_execute_step_raises_not_implemented():
    provider = BrowserOSAgentMotorProvider()
    step = AriadneStep(
        step_index=1,
        name="test",
        description="test",
        observe=AriadneObserve(),
        actions=[],
    )
    async with provider.open_session("sess") as session:
        with pytest.raises(NotImplementedError) as excinfo:
            await session.execute_step(
                step=step,
                context={},
                cv_path=Path("/tmp/cv.pdf"),
                letter_path=None,
                is_first=True,
                url="http://example.com",
            )
    assert "BrowserOS Agent motor is conceptual" in str(excinfo.value)


@pytest.mark.asyncio
async def test_begin_human_intervention_raises_not_implemented():
    provider = BrowserOSAgentMotorProvider()
    step = AriadneStep(
        step_index=1,
        name="test",
        description="test",
        observe=AriadneObserve(),
        actions=[],
    )
    async with provider.open_session("sess") as session:
        with pytest.raises(NotImplementedError) as excinfo:
            await session.begin_human_intervention(
                artifact_dir=Path("/tmp"),
                step=step,
                reason="test-reason",
            )
    assert "BrowserOS Agent motor is conceptual" in str(excinfo.value)


@pytest.mark.asyncio
async def test_inspect_danger_returns_default_report():
    provider = BrowserOSAgentMotorProvider()
    async with provider.open_session("sess") as session:
        report = await session.inspect_danger("http://example.com")
        assert report.primary is None
        assert report.findings == []
