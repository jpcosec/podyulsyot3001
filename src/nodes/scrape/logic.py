"""Scraping and preprocessing logic for ingestion stage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from src.nodes.scrape.contract import IngestedData
from src.core.tools.scraping.service import (
    detect_english_status,
    extract_source_text_markdown,
    fetch_html,
)


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Fetch source URL and produce cleaned markdown for downstream nodes."""
    source_url = _require_source_url(state)

    html = fetch_html(source_url)
    markdown_text = extract_source_text_markdown(html, url=source_url)
    lang_status = detect_english_status(markdown_text)

    ingested = IngestedData(
        source_url=source_url,
        original_language="en" if bool(lang_status.get("is_english")) else "non_en",
        raw_text=markdown_text,
        metadata={
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "marker_hits": int(lang_status.get("marker_hits", 0)),
            "has_umlaut": bool(lang_status.get("has_umlaut", False)),
        },
    )

    return {
        **dict(state),
        "current_node": "scrape",
        "status": "running",
        "ingested_data": ingested.model_dump(),
    }


def _require_source_url(state: Mapping[str, Any]) -> str:
    source_url = state.get("source_url")
    if not isinstance(source_url, str) or not source_url.strip():
        raise ValueError("state.source_url is required")
    return source_url
