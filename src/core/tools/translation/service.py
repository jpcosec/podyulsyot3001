"""Translation helpers for non-LLM bounded-nondeterministic steps."""

from __future__ import annotations

import time
from typing import Any, Callable, Protocol

from src.core.tools.errors import ToolDependencyError, ToolFailureError


class _Translator(Protocol):
    def translate(self, text: str) -> str: ...


TranslatorFactory = Callable[[str, str], _Translator]


def _default_translator_factory(source_lang: str, target_lang: str) -> _Translator:
    try:
        from deep_translator import GoogleTranslator
    except ImportError as exc:
        raise ToolDependencyError(
            "deep-translator is required for translation"
        ) from exc
    return GoogleTranslator(source=source_lang, target=target_lang)


def translate_text(
    text: str,
    *,
    target_lang: str,
    source_lang: str = "auto",
    translator_factory: TranslatorFactory | None = None,
    max_attempts: int = 2,
    retry_delay_seconds: float = 0.0,
) -> str:
    """Translate text with bounded retries and explicit failures."""
    if not text.strip():
        return text

    if source_lang == target_lang:
        return text

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    factory = translator_factory or _default_translator_factory
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            translator = factory(source_lang, target_lang)
            translated = translator.translate(text)
            return str(translated)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_attempts and retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)

    assert last_error is not None
    raise ToolFailureError(
        f"translation failed after {max_attempts} attempts"
    ) from last_error


def translate_fields(
    payload: dict[str, Any],
    *,
    fields: list[str],
    target_lang: str,
    source_lang: str = "auto",
    translator_factory: TranslatorFactory | None = None,
    max_attempts: int = 2,
    retry_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    """Translate selected top-level string fields in a payload."""
    out = dict(payload)
    for field in fields:
        value = out.get(field)
        if isinstance(value, str):
            out[field] = translate_text(
                value,
                target_lang=target_lang,
                source_lang=source_lang,
                translator_factory=translator_factory,
                max_attempts=max_attempts,
                retry_delay_seconds=retry_delay_seconds,
            )
    return out
