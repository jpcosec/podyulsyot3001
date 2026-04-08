"""Tests for BrowserOS MCP recording support."""

from __future__ import annotations

import json

from src.automation.motors.browseros.cli.client import BrowserOSClient
from src.automation.motors.browseros.cli.recording import BrowserOSMcpRecorder


class _FakeResponse:
    def __init__(self, payload: dict, headers: dict | None = None):
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse]):
        self.responses = list(responses)
        self.headers: dict[str, str] = {}
        self.requests: list[dict] = []

    def post(self, url: str, json: dict, timeout: float):
        self.requests.append({"url": url, "json": json, "timeout": timeout})
        return self.responses.pop(0)


def test_browseros_client_records_tool_calls_and_snapshots():
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "id": 1, "result": {}},
                headers={"Mcp-Session-Id": "sess-1"},
            ),
            _FakeResponse(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "content": [{"type": "text", "text": '[12] button "Apply"'}]
                    },
                }
            ),
        ]
    )
    recorder = BrowserOSMcpRecorder()
    client = BrowserOSClient(session=session, recorder=recorder)

    elements = client.take_snapshot(5)

    assert len(elements) == 1
    assert recorder.recording.calls[0].tool_name == "take_snapshot"
    assert recorder.recording.calls[0].arguments == {"page": 5}
    assert recorder.recording.snapshots[0].elements[0].text == "Apply"


def test_browseros_client_default_base_url_uses_stable_front_door():
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "id": 1, "result": {}},
                headers={"Mcp-Session-Id": "sess-1"},
            ),
            _FakeResponse({"jsonrpc": "2.0", "id": 2, "result": {}}),
        ]
    )
    client = BrowserOSClient(session=session)

    client.browseros_info()

    assert session.requests[0]["url"] == "http://127.0.0.1:9000/mcp"
