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


def test_browseros_client_uses_explicit_runtime_base_url():
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "id": 1, "result": {}},
                headers={"Mcp-Session-Id": "sess-1"},
            ),
            _FakeResponse({"jsonrpc": "2.0", "id": 2, "result": {}}),
        ]
    )
    client = BrowserOSClient(base_url="http://127.0.0.1:9201", session=session)

    client.browseros_info()

    assert session.requests[0]["url"] == "http://127.0.0.1:9201/mcp"


def test_browseros_client_exposes_high_value_interface_wrappers():
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "id": 1, "result": {}},
                headers={"Mcp-Session-Id": "sess-1"},
            ),
            _FakeResponse({"jsonrpc": "2.0", "id": 2, "result": {"content": []}}),
            _FakeResponse(
                {"jsonrpc": "2.0", "id": 3, "result": {"path": "/tmp/dom.html"}}
            ),
            _FakeResponse({"jsonrpc": "2.0", "id": 4, "result": {"text": "hello"}}),
            _FakeResponse({"jsonrpc": "2.0", "id": 5, "result": {}}),
            _FakeResponse({"jsonrpc": "2.0", "id": 6, "result": {}}),
        ]
    )
    client = BrowserOSClient(session=session)

    client.take_enhanced_snapshot(1)
    client.get_dom(1)
    client.get_page_content(1)
    client.focus(1, 5)
    client.handle_dialog(1, accept=True, prompt_text="yes")

    tool_names = [request["json"]["params"]["name"] for request in session.requests[1:]]
    assert tool_names == [
        "take_enhanced_snapshot",
        "get_dom",
        "get_page_content",
        "focus",
        "handle_dialog",
    ]
