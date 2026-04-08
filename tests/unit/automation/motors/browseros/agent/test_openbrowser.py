"""Tests for BrowserOS Level 2 /chat trace capture."""

from __future__ import annotations

from pathlib import Path

from src.automation.motors.browseros.agent.openbrowser import OpenBrowserClient


class _FakeResponse:
    def __init__(self, status_code: int, lines: list[str]):
        self.status_code = status_code
        self._lines = lines

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def iter_lines(self, decode_unicode: bool = True):
        yield from self._lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict, bool, float]] = []

    def post(self, url: str, json: dict, stream: bool, timeout: float):
        self.calls.append((url, json, stream, timeout))
        return self.response


def test_communicate_captures_chat_trace_and_writes_artifact(tmp_path: Path):
    session = _FakeSession(
        _FakeResponse(
            200,
            [
                'data: {"type":"start"}',
                'data: {"type":"text-start","id":"txt-0"}',
                'data: {"type":"text-delta","id":"txt-0","delta":"Ready."}',
                'data: {"type":"text-end","id":"txt-0"}',
                'data: {"type":"finish","finishReason":"stop"}',
                "data: [DONE]",
            ],
        )
    )
    client = OpenBrowserClient(base_url="http://127.0.0.1:9000", session=session)

    result = client.communicate(
        "Say only ready.",
        source="browseros",
        mode="chat",
        recording_path=tmp_path / "trace.json",
        timeout_seconds=5.0,
    )

    assert result.status == "success"
    assert result.final_text == "Ready."
    assert result.finish_reason == "stop"
    assert result.recording_path == str(tmp_path / "trace.json")
    assert (tmp_path / "trace.json").exists()
    assert session.calls[0][0] == "http://127.0.0.1:9000/chat"
    assert session.calls[0][1]["message"] == "Say only ready."


def test_communicate_captures_agent_tool_events():
    session = _FakeSession(
        _FakeResponse(
            200,
            [
                'data: {"type":"tool-input-start","toolCallId":"functions.get_active_page:0","toolName":"get_active_page"}',
                'data: {"type":"tool-input-available","toolCallId":"functions.get_active_page:0","toolName":"get_active_page","input":{}}',
                'data: {"type":"tool-output-available","toolCallId":"functions.get_active_page:0","output":{"content":[{"type":"text","text":"No active page found."}],"isError":true}}',
                'data: {"type":"finish","finishReason":"stop"}',
                "data: [DONE]",
            ],
        )
    )
    client = OpenBrowserClient(session=session)

    result = client.communicate(
        "Tell me the title of the active page.",
        source="demo",
        mode="agent",
        timeout_seconds=5.0,
    )

    assert result.status == "failed"
    assert result.error == "No active page found."
    event_types = [event.event_type for event in result.trace.stream_events]
    assert "tool-input-start" in event_types
    assert "tool-input-available" in event_types
    assert "tool-output-available" in event_types


def test_communicate_marks_rate_limit_without_raising():
    session = _FakeSession(_FakeResponse(429, []))
    client = OpenBrowserClient(session=session)

    result = client.communicate("hello", timeout_seconds=5.0)

    assert result.status == "rate_limited"
    assert result.error == "BrowserOS /chat rate limited the request."


def test_run_agent_returns_trace_metadata_without_playbook():
    session = _FakeSession(
        _FakeResponse(
            200,
            [
                'data: {"type":"text-start","id":"txt-0"}',
                'data: {"type":"text-delta","id":"txt-0","delta":"done"}',
                'data: {"type":"finish","finishReason":"stop"}',
                "data: [DONE]",
            ],
        )
    )
    client = OpenBrowserClient(session=session)

    result = client.run_agent("xing", "https://example.com", {"profile": {}})

    assert result.status == "capture_only"
    assert result.playbook is None
    assert result.conversation_id is not None
    assert result.candidates == []


def test_run_agent_includes_normalized_candidates_when_tool_events_exist():
    session = _FakeSession(
        _FakeResponse(
            200,
            [
                'data: {"type":"tool-input-available","toolCallId":"functions.navigate_page:0","toolName":"navigate_page","input":{"url":"https://example.com/apply"}}',
                'data: {"type":"finish","finishReason":"stop"}',
                "data: [DONE]",
            ],
        )
    )
    client = OpenBrowserClient(session=session)

    result = client.run_agent("xing", "https://example.com", {"profile": {}})

    assert result.status == "success"
    assert len(result.candidates) == 1
    assert result.candidates[0]["candidate_intent"] == "navigate"
    assert result.playbook is not None
    assert result.playbook.steps[0].actions[0].value == "https://example.com/apply"
