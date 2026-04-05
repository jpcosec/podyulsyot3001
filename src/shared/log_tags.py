"""Standardized log tag enum for consistent observability across all pipeline modules.

Import ``LogTag`` instead of writing emoji strings by hand. This prevents typos,
enforces the shared visual vocabulary, and makes log output grep-friendly.

Usage::

    import logging
    from src.shared.log_tags import LogTag

    logger = logging.getLogger(__name__)

    logger.info(f"{LogTag.LLM} Generating match proposal for {job_id}")
    logger.warning(f"{LogTag.WARN} Rate limit hit, retrying in {delay}s")
    logger.error(f"{LogTag.FAIL} Schema validation failed: {err}")
"""

from __future__ import annotations

from enum import StrEnum


class LogTag(StrEnum):
    """Bracketed emoji tags for structured log messages.

    Each tag maps to a single semantic meaning. Using the wrong tag for a context
    (e.g. LLM on a deterministic path) is a code review concern — the enum only
    prevents typos and enforces the shared vocabulary.

    Tags are formatted as ``[emoji]`` so they are visually scannable and
    grep-friendly (``grep '\\[🧠\\]'`` to find all LLM reasoning log lines).
    """

    SKIP = "[⏭️]"
    """Item skipped — already processed. Use for idempotency guards."""

    CACHE = "[📦]"
    """Cache hit or existing artifact loaded from disk."""

    LLM = "[🧠]"
    """LLM reasoning, dynamic generation, or semantic inference. Do NOT use on
    deterministic paths — that would misrepresent the execution trace."""

    FAST = "[⚡]"
    """Fast, deterministic logic path. No LLM involved."""

    FALLBACK = "[🤖]"
    """Fallback mechanism active (e.g. LLM rescue after regex failure)."""

    OK = "[✅]"
    """Successful validation or process step completed."""

    WARN = "[⚠️]"
    """Expected or handled error (rate limit, partial result). Pipeline continues."""

    FAIL = "[❌]"
    """Hard failure. Pipeline execution breaks. Use with logger.error()."""
