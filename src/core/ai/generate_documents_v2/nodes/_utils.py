"""Internal utilities shared across generate_documents_v2 nodes."""

from __future__ import annotations

import os

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _google_api_key() -> str | None:
    """Return the configured Google API key for Gemini-backed nodes."""
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def _gemini_model(stage: str) -> str:
    """Resolve the Gemini model name for a pipeline stage.

    Resolution order:
    1. ``GEMINI_MODEL_<STAGE>``
    2. ``GEMINI_MODEL``
    3. repository default ``gemini-2.5-flash``

    Args:
        stage: Logical stage name such as ``"ingestion"`` or ``"drafting"``.

    Returns:
        The configured Gemini model name for that stage.
    """
    stage_key = stage.upper().replace("-", "_")
    return (
        os.environ.get(f"GEMINI_MODEL_{stage_key}")
        or os.environ.get("GEMINI_MODEL")
        or DEFAULT_GEMINI_MODEL
    )
