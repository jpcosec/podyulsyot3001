from __future__ import annotations

from src.core.ai.generate_documents_v2.nodes._utils import (
    DEFAULT_GEMINI_MODEL,
    _gemini_model,
)


def test_gemini_model_defaults_to_repo_default(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL_INGESTION", raising=False)

    assert _gemini_model("ingestion") == DEFAULT_GEMINI_MODEL


def test_gemini_model_uses_global_env_default(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.delenv("GEMINI_MODEL_INGESTION", raising=False)

    assert _gemini_model("ingestion") == "gemini-2.5-pro"


def test_gemini_model_prefers_stage_override(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("GEMINI_MODEL_REQUIREMENT_FILTER", "gemini-2.5-pro")

    assert _gemini_model("requirement_filter") == "gemini-2.5-pro"


def test_gemini_model_normalizes_stage_name(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_MODEL_REQUIREMENT_FILTER", "gemini-2.5-pro")

    assert _gemini_model("requirement-filter") == "gemini-2.5-pro"
