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
    max_chunk_chars: int = 4500,
) -> str:
    """Translate text with bounded retries and explicit failures."""
    if not text.strip():
        return text

    if source_lang == target_lang:
        return text

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if max_chunk_chars < 50:
        raise ValueError("max_chunk_chars must be >= 50")

    factory = translator_factory or _default_translator_factory
    last_error: Exception | None = None

    chunks = _chunk_text(text, max_chars=max_chunk_chars)
    translated_chunks: list[str] = []
    for chunk in chunks:
        for attempt in range(1, max_attempts + 1):
            try:
                translator = factory(source_lang, target_lang)
                translated = translator.translate(chunk)
                translated_chunks.append(str(translated))
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < max_attempts and retry_delay_seconds > 0:
                    time.sleep(retry_delay_seconds)
        else:
            break

    if translated_chunks and len(translated_chunks) == len(chunks):
        return "\n".join(translated_chunks)

    assert last_error is not None
    raise ToolFailureError(
        f"translation failed after {max_attempts} attempts"
    ) from last_error


def _chunk_text(text: str, *, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.splitlines():
        line_len = len(line) + 1
        if line_len > max_chars:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            start = 0
            while start < len(line):
                end = min(start + max_chars, len(line))
                chunks.append(line[start:end])
                start = end
            continue

        if current_len + line_len > max_chars and current:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


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
