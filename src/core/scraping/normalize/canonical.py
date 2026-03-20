from __future__ import annotations

from typing import Any


def build_canonical_scrape(
    source: str,
    source_url: str,
    resolved_url: str,
    raw_text: str,
    job_id: str | None,
    warnings: list[str],
    artifact_refs: dict[str, str],
    original_language: str | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "source_url": source_url,
        "resolved_url": resolved_url,
        "job_id": job_id,
        "raw_text": raw_text,
        "original_language": original_language,
        "warnings": warnings,
        "artifact_refs": artifact_refs,
    }
