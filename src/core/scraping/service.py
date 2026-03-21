from __future__ import annotations

from pathlib import Path
import re
from typing import cast
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from src.core.io.workspace_manager import WorkspaceManager
from src.core.scraping.contracts import (
    CrawlListingRequest,
    CrawlListingResult,
    FetchMode,
    ScrapeDetailRequest,
    ScrapeDetailResult,
    UsedFetchMode,
)
from src.core.scraping.crawl.dedup import split_new_ids
from src.core.scraping.fetch.http_fetcher import HttpFetcher
from src.core.scraping.fetch.playwright_fetcher import PlaywrightFetcher
from src.core.scraping.fetch.policy import select_initial_mode
from src.core.scraping.normalize.canonical import build_canonical_scrape
from src.core.scraping.persistence.artifact_store import ScrapingArtifactStore
from src.core.scraping.registry import get_scraping_registry
from src.core.scraping.strategies.stepstone import (
    extract_stepstone_detail,
    extract_stepstone_listing_urls,
)
from src.core.scraping.extract.html_to_text import extract_text
from src.core.scraping.extract.quality import check_text_quality
from src.core.tools.errors import ToolFailureError

GENERIC_JOB_ID_RE = re.compile(r"/job-postings/(\d+)(?:[/?#]|$)")


def scrape_detail(request: ScrapeDetailRequest) -> ScrapeDetailResult:
    registry = get_scraping_registry()
    adapter = registry.resolve(request.source, request.source_url)
    job_id = request.job_id or adapter.extract_job_id(request.source_url) or "unknown"
    artifact_store = ScrapingArtifactStore()
    screenshot_path = WorkspaceManager().node_stage_artifact(
        request.source,
        job_id,
        "scrape",
        "trace",
        "error_screenshot.png",
    )

    warnings: list[str] = []
    fetch_result = _fetch_detail(
        source_url=request.source_url,
        preferred_mode=request.preferred_fetch_mode,
        browser_required=adapter.capabilities.browser_required,
        screenshot_path=screenshot_path,
        warnings=warnings,
    )

    source_extraction = _extract_detail_payload(
        request.source_url, fetch_result.content
    )
    raw_text = str(
        source_extraction.get("raw_text") or extract_text(fetch_result.content)
    )
    quality = check_text_quality(raw_text)
    warnings.extend(fetch_result.warnings)
    warnings.extend(quality.warnings)

    artifact_refs: dict[str, str] = {}
    artifact_refs["fetch_metadata"] = artifact_store.write_json(
        request.source,
        job_id,
        "input",
        "fetch_metadata.json",
        {
            "requested_url": request.source_url,
            "resolved_url": fetch_result.resolved_url,
            "status_code": fetch_result.status_code,
            "used_fetch_mode": fetch_result.mode,
            "warnings": warnings,
        },
    )
    artifact_refs["raw_snapshot"] = artifact_store.write_json(
        request.source,
        job_id,
        "input",
        "raw_snapshot.json",
        {
            "content": fetch_result.content,
            "resolved_url": fetch_result.resolved_url,
            "status_code": fetch_result.status_code,
        },
    )
    artifact_refs["source_extraction"] = artifact_store.write_json(
        request.source,
        job_id,
        "proposed",
        "source_extraction.json",
        source_extraction,
    )
    artifact_refs["source_markdown"] = artifact_store.write_raw_source_markdown(
        request.source,
        job_id,
        raw_text,
    )

    canonical = build_canonical_scrape(
        source=request.source,
        source_url=request.source_url,
        resolved_url=fetch_result.resolved_url,
        raw_text=raw_text,
        job_id=job_id,
        warnings=warnings,
        artifact_refs=artifact_refs,
        original_language=None,
    )
    canonical["metadata"] = {
        "source_extraction": source_extraction,
        "quality_warnings": quality.warnings,
    }
    artifact_refs["canonical_scrape"] = artifact_store.write_json(
        request.source,
        job_id,
        "approved",
        "canonical_scrape.json",
        canonical,
    )
    canonical["artifact_refs"] = artifact_refs

    return ScrapeDetailResult(
        canonical_scrape=canonical,
        artifact_refs=artifact_refs,
        warnings=warnings,
        used_fetch_mode=cast(UsedFetchMode, fetch_result.mode),
    )


def crawl_listing(request: CrawlListingRequest) -> CrawlListingResult:
    registry = get_scraping_registry()
    fetcher = HttpFetcher()
    discovered_urls: list[str] = []
    discovered_ids: list[str] = []
    warnings: list[str] = []
    seen_urls: set[str] = set()
    seen_ids: set[str] = set()

    for page in range(1, request.max_pages + 1):
        page_url = _listing_page_url(request.listing_url, page)
        fetch_result = fetcher.fetch(page_url, timeout_seconds=20.0)
        page_urls = _extract_listing_urls(
            request.source, page_url, fetch_result.content
        )
        if not page_urls:
            break
        page_ids: list[str] = []
        for discovered_url in page_urls:
            if discovered_url not in seen_urls:
                seen_urls.add(discovered_url)
                discovered_urls.append(discovered_url)
            detail_adapter = registry.resolve(None, discovered_url)
            job_id = detail_adapter.extract_job_id(discovered_url)
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                page_ids.append(job_id)
                discovered_ids.append(job_id)
        if not page_ids:
            break

    new_ids = split_new_ids(discovered_ids, request.known_ids)
    listing_job_id = request.run_id or "listing"
    artifact_store = ScrapingArtifactStore()
    artifact_refs = {
        "listing_crawl": artifact_store.write_json(
            request.source,
            listing_job_id,
            "meta",
            "listing_crawl.json",
            {
                "listing_url": request.listing_url,
                "discovered_urls": discovered_urls,
                "discovered_ids": discovered_ids,
                "known_ids": request.known_ids,
                "new_ids": new_ids,
                "warnings": warnings,
            },
        )
    }
    return CrawlListingResult(
        discovered_urls=discovered_urls,
        discovered_ids=discovered_ids,
        new_ids=new_ids,
        artifact_refs=artifact_refs,
        warnings=warnings,
    )


def _fetch_detail(
    *,
    source_url: str,
    preferred_mode: str,
    browser_required: bool,
    screenshot_path: Path,
    warnings: list[str],
):
    initial_mode = select_initial_mode(
        cast(FetchMode, preferred_mode), browser_required
    )
    if initial_mode == "playwright":
        return _fetch_with_playwright(source_url, screenshot_path)

    try:
        return HttpFetcher().fetch(source_url, timeout_seconds=20.0)
    except ToolFailureError:
        warnings.append("http_fetch_failed")
        return _fetch_with_playwright(source_url, screenshot_path)


def _fetch_with_playwright(source_url: str, screenshot_path: Path):
    fetcher = PlaywrightFetcher()
    try:
        return fetcher.fetch(
            source_url,
            timeout_seconds=30.0,
            error_screenshot_path=screenshot_path,
        )
    except TypeError:
        return fetcher.fetch(source_url, timeout_seconds=30.0)


def _extract_detail_payload(source_url: str, html: str) -> dict[str, object]:
    if "stepstone" in urlparse(source_url).netloc:
        return extract_stepstone_detail(html)
    return {"raw_text": extract_text(html)}


def _extract_listing_urls(source: str, page_url: str, html: str) -> list[str]:
    if source == "stepstone" or "stepstone" in urlparse(page_url).netloc:
        urls = extract_stepstone_listing_urls(html, page_url)
        if urls:
            return urls
    return _extract_generic_listing_urls(source, html)


def _extract_generic_listing_urls(source: str, html: str) -> list[str]:
    _ = source
    urls: list[str] = []
    for quote in ('"', "'"):
        marker = f"href={quote}"
        for chunk in html.split(marker):
            href = chunk.split(quote, 1)[0]
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://jobs.tu-berlin.de{href}"
            if GENERIC_JOB_ID_RE.search(href):
                urls.append(href)
    return urls


def _listing_page_url(base_url: str, page: int) -> str:
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["page"] = str(page)
    return urlunparse(parsed._replace(query=urlencode(query)))
