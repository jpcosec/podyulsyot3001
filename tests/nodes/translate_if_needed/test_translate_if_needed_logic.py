"""Tests for translation normalization logic."""

from __future__ import annotations

import pytest

from src.nodes.translate_if_needed.logic import run_logic


def test_run_logic_skips_translation_when_already_target_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"count": 0}

    def fake_translate(
        _text: str, *, target_lang: str, source_lang: str = "auto"
    ) -> str:
        called["count"] += 1
        return "translated"

    monkeypatch.setattr(
        "src.nodes.translate_if_needed.logic.translate_text", fake_translate
    )

    out = run_logic(
        {
            "ingested_data": {
                "original_language": "en",
                "raw_text": "Already English",
                "metadata": {},
            }
        }
    )

    assert called["count"] == 0
    assert out["ingested_data"]["raw_text"] == "Already English"
    assert out["ingested_data"]["metadata"]["translated"] is False


def test_run_logic_translates_when_non_english(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.nodes.translate_if_needed.logic.translate_text",
        lambda text, *, target_lang, source_lang="auto": f"{target_lang}:{text}",
    )

    out = run_logic(
        {
            "target_language": "en",
            "ingested_data": {
                "original_language": "non_en",
                "raw_text": "Hallo Welt",
                "metadata": {},
            },
        }
    )

    assert out["ingested_data"]["raw_text"] == "en:Hallo Welt"
    assert out["ingested_data"]["metadata"]["translated"] is True


def test_run_logic_requires_ingested_data() -> None:
    with pytest.raises(ValueError, match="ingested_data"):
        run_logic({"job_id": "job-1"})
