"""Translation stage that normalizes ingested text when needed."""

from __future__ import annotations

from typing import Any, Mapping

from src.core.tools.translation.service import translate_text


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Translate ingested raw text only when language is not English."""
    ingested_data = _require_ingested_data(state)
    raw_text = _require_raw_text(ingested_data)

    target_lang = _resolve_target_lang(state)
    original_language = ingested_data.get("original_language")
    needs_translation = original_language != target_lang

    translated_text = (
        translate_text(raw_text, target_lang=target_lang)
        if needs_translation
        else raw_text
    )

    metadata = ingested_data.get("metadata")
    metadata_out = dict(metadata) if isinstance(metadata, Mapping) else {}
    metadata_out["translated"] = needs_translation
    metadata_out["translated_to"] = target_lang

    updated_ingested = {
        **dict(ingested_data),
        "raw_text": translated_text,
        "metadata": metadata_out,
    }

    return {
        **dict(state),
        "current_node": "translate_if_needed",
        "status": "running",
        "ingested_data": updated_ingested,
    }


def _require_ingested_data(state: Mapping[str, Any]) -> Mapping[str, Any]:
    ingested = state.get("ingested_data")
    if not isinstance(ingested, Mapping):
        raise ValueError("state.ingested_data is required")
    return ingested


def _require_raw_text(ingested_data: Mapping[str, Any]) -> str:
    raw_text = ingested_data.get("raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("state.ingested_data.raw_text is required")
    return raw_text


def _resolve_target_lang(state: Mapping[str, Any]) -> str:
    target_lang = state.get("target_language", "en")
    if not isinstance(target_lang, str) or not target_lang.strip():
        raise ValueError("state.target_language must be a non-empty string")
    return target_lang
