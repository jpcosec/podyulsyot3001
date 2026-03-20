from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FetchMode = Literal["http", "playwright", "auto"]
UsedFetchMode = Literal["http", "playwright"]


@dataclass(frozen=True)
class ScrapeDetailRequest:
    source: str
    source_url: str
    job_id: str | None = None
    preferred_fetch_mode: FetchMode = "auto"
    run_id: str | None = None


@dataclass(frozen=True)
class ScrapeDetailResult:
    canonical_scrape: dict[str, Any]
    artifact_refs: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    used_fetch_mode: UsedFetchMode = "http"


@dataclass(frozen=True)
class CrawlListingRequest:
    source: str
    listing_url: str
    known_ids: list[str] = field(default_factory=list)
    max_pages: int = 1
    run_id: str | None = None


@dataclass(frozen=True)
class CrawlListingResult:
    discovered_urls: list[str]
    discovered_ids: list[str]
    new_ids: list[str]
    artifact_refs: dict[str, str]
    warnings: list[str] = field(default_factory=list)
