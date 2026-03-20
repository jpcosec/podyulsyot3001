from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast
from urllib.parse import urljoin, urlparse, urlunparse
import re

from src.core.scraping.contracts import (
    CrawlListingRequest,
    CrawlListingResult,
    FetchMode,
    ScrapeDetailRequest,
    ScrapeDetailResult,
)
from src.core.scraping.crawl.dedup import split_new_ids
from src.core.scraping.extract.html_to_text import extract_text
from src.core.scraping.extract.quality import check_text_quality
from src.core.scraping.fetch.base import FetchResult
from src.core.scraping.fetch.http_fetcher import HttpFetcher
from src.core.scraping.fetch.playwright_fetcher import PlaywrightFetcher
from src.core.scraping.fetch.policy import select_initial_mode
from src.core.scraping.normalize.canonical import build_canonical_scrape
from src.core.scraping.persistence.artifact_store import ScrapingArtifactStore
from src.core.scraping.contracts import (
    UsedFetchMode,
)
from src.core.scraping.registry import get_scraping_registry
from src.core.scraping.adapters.base import SourceAdapter
from src.core.scraping.strategies.stepstone import (
    extract_stepstone_detail,
    extract_stepstone_listing_urls,
)
from src.core.tools.errors import ToolDependencyError, ToolFailureError
from src.core.tools.scraping.service import (
    build_listing_page_url,
    detect_english_status,
    extract_job_ids_from_listing_html,
    extract_source_text_markdown,
)

DEFAULT_TIMEOUT_SECONDS = 20.0
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', flags=re.IGNORECASE)


def scrape_detail(request: ScrapeDetailRequest) -> ScrapeDetailResult:
    registry = get_scraping_registry()
    adapter = registry.resolve(source=request.source, url=request.source_url)
    inferred_job_id = request.job_id or adapter.extract_job_id(request.source_url)

    mode = select_initial_mode(
        preferred_mode=request.preferred_fetch_mode,
        browser_required=adapter.capabilities.browser_required,
    )
    fetch_result, warnings = _fetch_with_fallback(
        url=request.source_url,
        preferred_mode=request.preferred_fetch_mode,
        initial_mode=mode,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    extracted_text = extract_text(fetch_result.content)
    source_payload: dict[str, Any] = {}
    if adapter.capabilities.source_key == "stepstone":
        source_payload = extract_stepstone_detail(fetch_result.content)
        candidate_text = source_payload.get("raw_text")
        if isinstance(candidate_text, str) and len(candidate_text.strip()) >= 300:
            extracted_text = candidate_text
        elif isinstance(candidate_text, str) and candidate_text.strip():
            warnings.append("stepstone_structured_too_short_fallback_generic")

    quality = check_text_quality(extracted_text)
    warnings.extend(quality.warnings)

    lang_status = detect_english_status(extracted_text)
    original_language = "en" if bool(lang_status.get("is_english")) else "non_en"

    metadata = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "marker_hits": _coerce_int(lang_status.get("marker_hits"), default=0),
        "has_umlaut": bool(lang_status.get("has_umlaut", False)),
        "adapter": adapter.capabilities.source_key,
        "fetch_mode": fetch_result.mode,
        "http_status": fetch_result.status_code,
    }
    artifact_refs = _write_detail_artifacts(
        request=request,
        fetch_result=fetch_result,
        extracted_text=extracted_text,
        source_payload=source_payload,
        metadata=metadata,
        warnings=warnings,
        inferred_job_id=inferred_job_id,
    )
    canonical_scrape = build_canonical_scrape(
        source=request.source,
        source_url=request.source_url,
        resolved_url=fetch_result.resolved_url,
        raw_text=extracted_text,
        job_id=inferred_job_id,
        warnings=warnings,
        artifact_refs=artifact_refs,
        original_language=original_language,
    )
    canonical_scrape["metadata"] = metadata
    if source_payload:
        canonical_scrape["source_payload"] = source_payload

    return ScrapeDetailResult(
        canonical_scrape=canonical_scrape,
        artifact_refs=artifact_refs,
        warnings=warnings,
        used_fetch_mode=_to_used_fetch_mode(fetch_result.mode),
    )


def crawl_listing(request: CrawlListingRequest) -> CrawlListingResult:
    adapter = get_scraping_registry().resolve(
        source=request.source, url=request.listing_url
    )
    discovered_urls: list[str] = []
    discovered_ids: list[str] = []
    warnings: list[str] = []

    if not adapter.capabilities.supports_listing:
        warnings.append("listing_not_supported_for_source")
    else:
        for page in range(1, max(request.max_pages, 1) + 1):
            page_url = build_listing_page_url(request.listing_url, page)
            try:
                fetch_result = HttpFetcher().fetch(
                    page_url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS
                )
            except ToolFailureError:
                warnings.append(f"listing_fetch_failed:{page}")
                break
            page_urls = _extract_listing_detail_urls(
                html=fetch_result.content,
                base_url=fetch_result.resolved_url,
                adapter=adapter,
            )
            if adapter.capabilities.source_key == "stepstone":
                stepstone_urls = extract_stepstone_listing_urls(
                    fetch_result.content,
                    fetch_result.resolved_url,
                )
                page_urls = _dedupe_urls(stepstone_urls + page_urls)
            if not page_urls:
                try:
                    browser_fetch = PlaywrightFetcher().fetch(
                        page_url,
                        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                    )
                except (ToolDependencyError, ToolFailureError):
                    browser_fetch = None
                if browser_fetch is not None:
                    page_urls = _extract_listing_detail_urls(
                        html=browser_fetch.content,
                        base_url=browser_fetch.resolved_url,
                        adapter=adapter,
                    )
                    if adapter.capabilities.source_key == "stepstone":
                        stepstone_urls = extract_stepstone_listing_urls(
                            browser_fetch.content,
                            browser_fetch.resolved_url,
                        )
                        page_urls = _dedupe_urls(stepstone_urls + page_urls)
                    warnings.extend(browser_fetch.warnings)

            page_ids = sorted(
                {
                    job_id
                    for job_id in (adapter.extract_job_id(url) for url in page_urls)
                    if job_id
                }
            )
            if not page_ids:
                break
            discovered_ids.extend(page_ids)
            discovered_urls.extend(page_urls)

    new_ids = split_new_ids(discovered_ids=discovered_ids, known_ids=request.known_ids)
    artifact_refs = _write_listing_artifacts(
        request=request,
        discovered_ids=discovered_ids,
        discovered_urls=discovered_urls,
        new_ids=new_ids,
        warnings=warnings,
    )
    return CrawlListingResult(
        discovered_urls=discovered_urls,
        discovered_ids=discovered_ids,
        new_ids=new_ids,
        artifact_refs=artifact_refs,
        warnings=warnings,
    )


def _fetch_with_fallback(
    url: str,
    preferred_mode: FetchMode,
    initial_mode: UsedFetchMode,
    timeout_seconds: float,
) -> tuple[FetchResult, list[str]]:
    warnings: list[str] = []
    ordered_modes: list[UsedFetchMode] = [initial_mode]
    if preferred_mode == "auto" and initial_mode == "http":
        ordered_modes.append("playwright")

    last_error: Exception | None = None
    for mode in ordered_modes:
        try:
            fetcher = _get_fetcher(mode)
            result = fetcher.fetch(url, timeout_seconds=timeout_seconds)
            warnings.extend(result.warnings)
            return result, warnings
        except ToolDependencyError as exc:
            warnings.append(f"{mode}_dependency_missing")
            last_error = exc
        except ToolFailureError as exc:
            warnings.append(f"{mode}_fetch_failed")
            last_error = exc

    if last_error is not None:
        raise ToolFailureError(f"all fetch modes failed: {url}") from last_error
    raise ToolFailureError(f"no fetch mode available: {url}")


def _get_fetcher(mode: UsedFetchMode):
    if mode == "playwright":
        return PlaywrightFetcher()
    return HttpFetcher()


def _write_detail_artifacts(
    request: ScrapeDetailRequest,
    fetch_result: FetchResult,
    extracted_text: str,
    source_payload: dict[str, Any],
    metadata: dict[str, Any],
    warnings: list[str],
    inferred_job_id: str | None,
) -> dict[str, str]:
    if not inferred_job_id:
        return {}

    store = ScrapingArtifactStore()
    source = request.source
    job_id = inferred_job_id
    refs = {
        "fetch_metadata": store.write_json(
            source=source,
            job_id=job_id,
            stage="input",
            filename="fetch_metadata.json",
            payload={
                "requested_url": request.source_url,
                "resolved_url": fetch_result.resolved_url,
                "status_code": fetch_result.status_code,
                "fetch_mode": fetch_result.mode,
                "warnings": warnings,
            },
        ),
        "raw_snapshot": store.write_json(
            source=source,
            job_id=job_id,
            stage="input",
            filename="raw_snapshot.json",
            payload={
                "url": fetch_result.resolved_url,
                "content_length": len(fetch_result.content),
                "content": fetch_result.content,
            },
        ),
        "source_extraction": store.write_json(
            source=source,
            job_id=job_id,
            stage="proposed",
            filename="source_extraction.json",
            payload={
                "source": source,
                "source_url": request.source_url,
                "resolved_url": fetch_result.resolved_url,
                "raw_text": extracted_text,
                "warnings": warnings,
                "metadata": metadata,
                "source_payload": source_payload,
            },
        ),
    }
    refs["canonical_scrape"] = store.write_json(
        source=source,
        job_id=job_id,
        stage="approved",
        filename="canonical_scrape.json",
        payload={
            "source": source,
            "source_url": request.source_url,
            "resolved_url": fetch_result.resolved_url,
            "job_id": inferred_job_id,
            "raw_text": extracted_text,
            "original_language": "en" if metadata["marker_hits"] <= 1 else "non_en",
            "metadata": metadata,
            "warnings": warnings,
            "source_payload": source_payload,
        },
    )
    markdown_content = extract_source_text_markdown(
        fetch_result.content, url=request.source_url
    )
    source_text = source_payload.get("raw_text")
    if isinstance(source_text, str) and len(source_text.strip()) >= 300:
        markdown_content = _build_markdown_from_text(request.source_url, source_text)

    refs["source_markdown"] = store.write_raw_source_markdown(
        source=source,
        job_id=job_id,
        content=markdown_content,
    )
    return refs


def _write_listing_artifacts(
    request: CrawlListingRequest,
    discovered_ids: list[str],
    discovered_urls: list[str],
    new_ids: list[str],
    warnings: list[str],
) -> dict[str, str]:
    synthetic_job_id = _listing_job_id(request)
    store = ScrapingArtifactStore()
    path = store.write_json(
        source=request.source,
        job_id=synthetic_job_id,
        stage="input",
        filename="listing_crawl.json",
        payload={
            "listing_url": request.listing_url,
            "known_ids": request.known_ids,
            "discovered_ids": discovered_ids,
            "discovered_urls": discovered_urls,
            "new_ids": new_ids,
            "warnings": warnings,
        },
    )
    return {"listing_crawl": path}


def _extract_listing_detail_urls(
    html: str,
    base_url: str,
    adapter: SourceAdapter,
) -> list[str]:
    discovered: list[str] = []
    seen: set[str] = set()

    for href in HREF_RE.findall(html):
        normalized = _normalize_url(urljoin(base_url, href))
        if not normalized:
            continue
        job_id = adapter.extract_job_id(normalized)
        if job_id:
            if normalized not in seen:
                seen.add(normalized)
                discovered.append(normalized)
            continue

        if not normalized.startswith("https://"):
            continue
        if (
            "stepstone.de/stellenangebote--" in normalized
            and "-inline.html" in normalized
        ):
            job_id = adapter.extract_job_id(normalized)
            if job_id and normalized not in seen:
                seen.add(normalized)
                discovered.append(normalized)

    generic_ids = sorted(extract_job_ids_from_listing_html(html))
    for job_id in generic_ids:
        built = adapter.build_detail_url(job_id)
        if built and built not in seen:
            seen.add(built)
            discovered.append(built)
    return discovered


def _normalize_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    cleaned = parsed._replace(query="", fragment="")
    return urlunparse(cleaned)


def _dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            output.append(url)
    return output


def _build_markdown_from_text(source_url: str, raw_text: str) -> str:
    lines = [
        "# Scraped Source Text",
        "",
        f"- URL: {source_url}",
        "",
        "## Main Content",
        raw_text,
        "",
    ]
    return "\n".join(lines)


def _to_used_fetch_mode(value: str) -> UsedFetchMode:
    if value == "playwright":
        return cast(UsedFetchMode, "playwright")
    return cast(UsedFetchMode, "http")


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _listing_job_id(request: CrawlListingRequest) -> str:
    if request.run_id:
        return f"listing-{request.run_id}"
    if request.known_ids:
        return request.known_ids[0]
    return "listing"
