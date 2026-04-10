"""Tests for BrowserOS MCP client helpers."""

from __future__ import annotations

from unittest.mock import patch
from src.automation.motors.browseros.cli.client import BrowserOSClient


class _FakeResponse:
    def __init__(self, payload, headers=None):
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return self.responses.pop(0)


@patch("src.automation.motors.browseros.cli.client.ensure_browseros_running")
def test_initialize_stores_mcp_session_header(mock_ensure):
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "result": {}}, headers={"Mcp-Session-Id": "abc123"}
            )
        ]
    )
    client = BrowserOSClient(session=session)

    client.initialize()

    assert session.headers["Mcp-Session-Id"] == "abc123"


@patch("src.automation.motors.browseros.cli.client.ensure_browseros_running")
def test_take_snapshot_parses_interactive_elements(mock_ensure):
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "result": {}}, headers={"Mcp-Session-Id": "abc123"}
            ),
            _FakeResponse(
                {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": '[124] button "LinkedIn"\n[512] textbox "First name"',
                            }
                        ]
                    },
                }
            ),
        ]
    )
    client = BrowserOSClient(session=session)

    snapshot = client.take_snapshot(7)

    assert [element.element_id for element in snapshot] == [124, 512]
    assert snapshot[1].text == "First name"


@patch("src.automation.motors.browseros.cli.client.ensure_browseros_running")
def test_evaluate_script_react_uses_evaluate_script_tool(mock_ensure):
    session = _FakeSession(
        [
            _FakeResponse(
                {"jsonrpc": "2.0", "result": {}}, headers={"Mcp-Session-Id": "abc123"}
            ),
            _FakeResponse({"jsonrpc": "2.0", "result": {}}),
        ]
    )
    client = BrowserOSClient(session=session)

    client.evaluate_script_react(42, "input[name='salary']", "65000")

    second_call = session.calls[1]["json"]
    assert second_call["params"]["name"] == "evaluate_script"
    expression = second_call["params"]["arguments"]["expression"]
    assert "input[name='salary']" in expression
    assert "65000" in expression
