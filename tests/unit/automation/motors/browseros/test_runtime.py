"""Tests for BrowserOS runtime endpoint resolution and health management."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from src.automation.motors.browseros.runtime import (
    resolve_browseros_runtime,
    is_runtime_ready,
    ensure_browseros_running,
)


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


def test_is_runtime_ready_returns_true_on_200():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        assert is_runtime_ready("http://example.com") is True


def test_is_runtime_ready_returns_false_on_failure():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("failed")
        assert is_runtime_ready("http://example.com") is False


def test_ensure_browseros_running_skips_if_ready():
    runtime = resolve_browseros_runtime()
    with patch("src.automation.motors.browseros.runtime.is_runtime_ready", return_value=True):
        with patch("subprocess.Popen") as mock_popen:
            ensure_browseros_running(runtime)
            mock_popen.assert_not_called()


def test_ensure_browseros_running_launches_if_unreachable():
    runtime = resolve_browseros_runtime()
    # First call False, then True after launch
    with patch("src.automation.motors.browseros.runtime.is_runtime_ready", side_effect=[False, True]):
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                ensure_browseros_running(runtime, timeout_seconds=1)
                mock_popen.assert_called_once()
                # Check --no-sandbox is passed
                args, _ = mock_popen.call_args
                assert "--no-sandbox" in args[0]
                assert "/home/jp/BrowserOS.AppImage" in args[0]


def test_ensure_browseros_running_prefers_env_path(monkeypatch):
    monkeypatch.setenv("BROWSEROS_APPIMAGE_PATH", "/tmp/MyBrowser.AppImage")
    runtime = resolve_browseros_runtime()
    
    with patch("src.automation.motors.browseros.runtime.is_runtime_ready", side_effect=[False, True]):
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                ensure_browseros_running(runtime, timeout_seconds=1)
                mock_popen.assert_called_once()
                args, _ = mock_popen.call_args
                assert "/tmp/MyBrowser.AppImage" in args[0]


def test_ensure_browseros_running_logs_error_on_timeout():
    runtime = resolve_browseros_runtime()
    # Always unreachable
    with patch("src.automation.motors.browseros.runtime.is_runtime_ready", return_value=False):
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.Popen"):
                with patch("time.sleep"):  # Skip sleep
                    with patch("src.automation.motors.browseros.runtime.logger.error") as mock_error:
                        ensure_browseros_running(runtime, timeout_seconds=0)  # Instant timeout
                        mock_error.assert_called_with("Timed out waiting for BrowserOS MCP at %s", runtime.mcp_url)
