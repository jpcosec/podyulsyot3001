"""Unit tests for BrowserOSAgentMotorProvider / BrowserOSAgentMotorSession."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.automation.ariadne.models import AriadneObserve, AriadneStep
from src.automation.motors.browseros.agent.openbrowser import (
    OpenBrowserAgentResult,
    OpenBrowserConversationResult,
)
from src.automation.motors.browseros.agent.provider import (
    BrowserOSAgentMotorProvider,
    BrowserOSAgentMotorSession,
)


class _FakeOpenBrowserClient:
    def __init__(self):
        self.calls: list[tuple] = []

    def communicate(self, prompt: str, **kwargs):
        self.calls.append(("communicate", prompt, kwargs))
        return OpenBrowserConversationResult(
            status="success",
            conversation_id="conv-1",
            trace={
                "conversation_id": "conv-1",
                "source": kwargs.get("source", "browseros"),
                "goal": prompt,
                "provider": "browseros",
                "model": "browseros-auto",
                "mode": "agent",
                "started_at": "2026-04-08T00:00:00+00:00",
                "stream_events": [],
            },
        )

    def run_agent(self, portal: str, url: str, context: dict):
        self.calls.append(("run_agent", portal, url, context))
        return OpenBrowserAgentResult(status="capture_only", conversation_id="conv-2")


def test_provider_is_instantiable():
    provider = BrowserOSAgentMotorProvider()
    assert hasattr(provider, "open_session")


@pytest.mark.asyncio
async def test_open_session_returns_session():
    provider = BrowserOSAgentMotorProvider(client_factory=_FakeOpenBrowserClient)

    async with provider.open_session("test-session") as session:
        assert isinstance(session, BrowserOSAgentMotorSession)
        assert hasattr(session, "observe")
        assert hasattr(session, "execute_step")
        assert hasattr(session, "inspect_danger")
        assert hasattr(session, "begin_human_intervention")


@pytest.mark.asyncio
async def test_observe_raises_not_implemented():
    provider = BrowserOSAgentMotorProvider(client_factory=_FakeOpenBrowserClient)
    async with provider.open_session("sess") as session:
        with pytest.raises(NotImplementedError) as excinfo:
            await session.observe({"#any-selector"})
    assert "BrowserOS Agent motor is conceptual" in str(excinfo.value)


@pytest.mark.asyncio
async def test_execute_step_raises_not_implemented():
    provider = BrowserOSAgentMotorProvider(client_factory=_FakeOpenBrowserClient)
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
    provider = BrowserOSAgentMotorProvider(client_factory=_FakeOpenBrowserClient)
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
    provider = BrowserOSAgentMotorProvider(client_factory=_FakeOpenBrowserClient)
    async with provider.open_session("sess") as session:
        report = await session.inspect_danger("http://example.com")
        assert report.primary is None
        assert report.findings == []


@pytest.mark.asyncio
async def test_capture_goal_delegates_to_openbrowser_client():
    fake = _FakeOpenBrowserClient()
    session = BrowserOSAgentMotorSession(client=fake)

    result = await session.capture_goal(
        "Explore the application flow",
        source="xing",
        recording_path=Path("/tmp/trace.json"),
        browser_context={"entry_url": "https://example.com"},
    )

    assert result.status == "success"
    assert fake.calls[0][0] == "communicate"
    assert fake.calls[0][1] == "Explore the application flow"
    assert fake.calls[0][2]["source"] == "xing"


@pytest.mark.asyncio
async def test_discover_path_delegates_to_openbrowser_client():
    fake = _FakeOpenBrowserClient()
    session = BrowserOSAgentMotorSession(client=fake)

    result = await session.discover_path(
        portal="xing",
        url="https://example.com/apply",
        context={"profile": {}},
    )

    assert result.status == "capture_only"
    assert fake.calls[0] == (
        "run_agent",
        "xing",
        "https://example.com/apply",
        {"profile": {}},
    )
