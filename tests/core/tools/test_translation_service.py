from __future__ import annotations

import pytest

from src.core.tools.errors import ToolFailureError
from src.core.tools.translation.service import translate_fields, translate_text


class _FakeTranslator:
    def __init__(self, translated: str):
        self.translated = translated

    def translate(self, text: str) -> str:
        return f"{self.translated}:{text}"


def test_translate_text_returns_input_when_same_language() -> None:
    assert translate_text("hola", source_lang="es", target_lang="es") == "hola"


def test_translate_text_uses_factory() -> None:
    def factory(_source: str, _target: str) -> _FakeTranslator:
        return _FakeTranslator("en")

    assert (
        translate_text(
            "hola", source_lang="es", target_lang="en", translator_factory=factory
        )
        == "en:hola"
    )


def test_translate_text_retries_then_succeeds() -> None:
    calls = {"count": 0}

    class _Flaky:
        def translate(self, text: str) -> str:
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("temporary")
            return f"ok:{text}"

    def factory(_source: str, _target: str) -> _Flaky:
        return _Flaky()

    assert (
        translate_text(
            "hola",
            source_lang="es",
            target_lang="en",
            translator_factory=factory,
            max_attempts=2,
        )
        == "ok:hola"
    )


def test_translate_text_raises_after_max_attempts() -> None:
    class _Broken:
        def translate(self, _text: str) -> str:
            raise RuntimeError("down")

    def factory(_source: str, _target: str) -> _Broken:
        return _Broken()

    with pytest.raises(ToolFailureError):
        translate_text(
            "hola",
            source_lang="es",
            target_lang="en",
            translator_factory=factory,
            max_attempts=2,
        )


def test_translate_fields_only_translates_selected_string_fields() -> None:
    def factory(_source: str, _target: str) -> _FakeTranslator:
        return _FakeTranslator("en")

    payload = {"title": "Hallo", "count": 3, "description": "Text"}
    out = translate_fields(
        payload,
        fields=["title"],
        source_lang="de",
        target_lang="en",
        translator_factory=factory,
    )

    assert out["title"] == "en:Hallo"
    assert out["description"] == "Text"
    assert out["count"] == 3
