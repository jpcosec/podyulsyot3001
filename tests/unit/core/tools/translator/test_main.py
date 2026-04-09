"""Tests for translator CLI entrypoints."""

from __future__ import annotations

from src.core.tools.translator import main as translator_main_module


def test_translator_main_accepts_target_lang_alias(tmp_path, monkeypatch) -> None:
    source_dir = tmp_path / "jobs" / "xing"
    source_dir.mkdir(parents=True)

    monkeypatch.setattr(
        translator_main_module, "configure_logging", lambda **kwargs: None
    )

    class _StubAdapter:
        def translate_fields(self, data, fields, target_lang, source_lang):
            return data

        def translate_text(self, text, target_lang, source_lang):
            return text

    monkeypatch.setattr(translator_main_module, "PROVIDERS", {"google": _StubAdapter()})

    exit_code = translator_main_module.main(
        [
            "--source",
            "xing",
            "--target-lang",
            "en",
            "--data_dir",
            str(tmp_path / "jobs"),
        ]
    )

    assert exit_code == 0
