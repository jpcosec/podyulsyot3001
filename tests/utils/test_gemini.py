import pytest
from unittest.mock import patch

try:
    from src.utils.gemini import GeminiClient
except ImportError as e:
    pytestmark = pytest.mark.skip(reason=f"google.generativeai not installed: {e}")


def test_gemini_client_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        GeminiClient()


def test_gemini_client_reads_model_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    with patch("src.utils.gemini.genai"):
        client = GeminiClient()
    assert client.model_name == "gemini-test-model"


def test_gemini_client_defaults_model(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    with patch("src.utils.gemini.genai"):
        client = GeminiClient()
    assert client.model_name == "gemini-2.5-flash"
