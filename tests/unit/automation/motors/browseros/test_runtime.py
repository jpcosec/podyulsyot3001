"""Tests for BrowserOS runtime endpoint resolution."""

from __future__ import annotations

from src.automation.motors.browseros.runtime import resolve_browseros_runtime


def test_runtime_defaults_to_stable_local_front_door(monkeypatch):
    monkeypatch.delenv("BROWSEROS_BASE_URL", raising=False)

    runtime = resolve_browseros_runtime()

    assert runtime.base_http_url == "http://127.0.0.1:9000"
    assert runtime.mcp_url == "http://127.0.0.1:9000/mcp"
    assert runtime.chat_url == "http://127.0.0.1:9000/chat"


def test_runtime_prefers_explicit_base_url(monkeypatch):
    monkeypatch.setenv("BROWSEROS_BASE_URL", "http://127.0.0.1:9999")

    runtime = resolve_browseros_runtime(preferred_base_url="http://127.0.0.1:9201")

    assert runtime.base_http_url == "http://127.0.0.1:9201"
    assert runtime.mcp_url == "http://127.0.0.1:9201/mcp"
    assert runtime.chat_url == "http://127.0.0.1:9201/chat"


def test_runtime_uses_environment_when_explicit_value_missing(monkeypatch):
    monkeypatch.setenv("BROWSEROS_BASE_URL", "http://127.0.0.1:9201")

    runtime = resolve_browseros_runtime()

    assert runtime.base_http_url == "http://127.0.0.1:9201"
    assert runtime.mcp_url == "http://127.0.0.1:9201/mcp"
