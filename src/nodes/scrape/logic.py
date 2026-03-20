from __future__ import annotations

from typing import Any, Mapping

from src.core.scraping.contracts import ScrapeDetailRequest
from src.core.scraping.service import scrape_detail
from src.nodes.scrape.contract import IngestedData


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    source_url = _require_source_url(state)
    source = _read_source(state)
    detail = scrape_detail(
        ScrapeDetailRequest(
            source=source,
            source_url=source_url,
            job_id=_read_optional_job_id(state),
        )
    )
    canonical = detail.canonical_scrape
    metadata = _read_metadata(canonical)
    metadata["artifact_refs"] = detail.artifact_refs
    metadata["scraping_warnings"] = detail.warnings

    ingested = IngestedData(
        source_url=source_url,
        original_language=str(canonical.get("original_language") or "non_en"),
        raw_text=str(canonical.get("raw_text") or ""),
        metadata=metadata,
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


def _read_source(state: Mapping[str, Any]) -> str:
    source = state.get("source")
    if isinstance(source, str) and source.strip():
        return source
    return "unknown"


def _read_optional_job_id(state: Mapping[str, Any]) -> str | None:
    job_id = state.get("job_id")
    if isinstance(job_id, str) and job_id.strip():
        return job_id
    return None


def _read_metadata(canonical: Mapping[str, Any]) -> dict[str, Any]:
    payload = canonical.get("metadata")
    if isinstance(payload, dict):
        return dict(payload)
    return {}
