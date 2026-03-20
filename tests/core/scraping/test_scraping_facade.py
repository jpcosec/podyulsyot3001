from __future__ import annotations

import pytest

from src.core.scraping.contracts import CrawlListingRequest, ScrapeDetailRequest
from src.core.scraping.fetch.base import FetchResult
from src.core.scraping.service import crawl_listing, scrape_detail
from src.core.tools.errors import ToolFailureError


def test_scrape_detail_http_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.core.scraping.service.HttpFetcher.fetch",
        lambda _self, _url, timeout_seconds: FetchResult(
            url="https://example.org/job/1",
            resolved_url="https://example.org/job/1",
            status_code=200,
            content="<html><body><h1>Role</h1><p>Long enough content for extraction.</p></body></html>",
            mode="http",
            warnings=[],
        ),
    )
    monkeypatch.setattr(
        "src.core.scraping.service.ScrapingArtifactStore.write_json",
        lambda _self, source, job_id, stage, filename, payload: (
            f"/tmp/{source}/{job_id}/{stage}/{filename}"
        ),
    )
    monkeypatch.setattr(
        "src.core.scraping.service.ScrapingArtifactStore.write_raw_source_markdown",
        lambda _self,
        source,
        job_id,
        content: f"/tmp/{source}/{job_id}/raw/source_text.md",
    )

    result = scrape_detail(
        ScrapeDetailRequest(
            source="stepstone",
            source_url="https://www.stepstone.de/stellenangebote--x--123-inline.html",
            job_id="123",
        )
    )

    assert result.used_fetch_mode == "http"
    assert "Role" in result.canonical_scrape["raw_text"]
    assert "canonical_scrape" in result.artifact_refs
    assert result.artifact_refs["source_markdown"].endswith("raw/source_text.md")


def test_scrape_detail_falls_back_to_playwright(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_http(_self, _url: str, timeout_seconds: float) -> FetchResult:
        raise ToolFailureError("fail")

    monkeypatch.setattr("src.core.scraping.service.HttpFetcher.fetch", fail_http)
    monkeypatch.setattr(
        "src.core.scraping.service.PlaywrightFetcher.fetch",
        lambda _self, _url, timeout_seconds: FetchResult(
            url="https://example.org/job/1",
            resolved_url="https://example.org/job/1",
            status_code=200,
            content="<html><body><h1>Role</h1><p>Fallback content from browser rendering.</p></body></html>",
            mode="playwright",
            warnings=[],
        ),
    )
    monkeypatch.setattr(
        "src.core.scraping.service.ScrapingArtifactStore.write_json",
        lambda _self, source, job_id, stage, filename, payload: (
            f"/tmp/{source}/{job_id}/{stage}/{filename}"
        ),
    )
    monkeypatch.setattr(
        "src.core.scraping.service.ScrapingArtifactStore.write_raw_source_markdown",
        lambda _self,
        source,
        job_id,
        content: f"/tmp/{source}/{job_id}/raw/source_text.md",
    )

    result = scrape_detail(
        ScrapeDetailRequest(
            source="stepstone",
            source_url="https://www.stepstone.de/stellenangebote--x--123-inline.html",
            preferred_fetch_mode="auto",
            job_id="123",
        )
    )

    assert result.used_fetch_mode == "playwright"
    assert "http_fetch_failed" in result.warnings


def test_crawl_listing_discovers_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(_self, url: str, timeout_seconds: float) -> FetchResult:
        if "page=1" in url:
            html = '<a href="/job-postings/101">A</a><a href="/job-postings/102">B</a>'
        else:
            html = ""
        return FetchResult(
            url=url,
            resolved_url=url,
            status_code=200,
            content=html,
            mode="http",
            warnings=[],
        )

    monkeypatch.setattr("src.core.scraping.service.HttpFetcher.fetch", fake_fetch)
    monkeypatch.setattr(
        "src.core.scraping.service.ScrapingArtifactStore.write_json",
        lambda _self, source, job_id, stage, filename, payload: (
            f"/tmp/{source}/{job_id}/{stage}/{filename}"
        ),
    )

    result = crawl_listing(
        CrawlListingRequest(
            source="stepstone",
            listing_url="https://www.stepstone.de/work",
            known_ids=["101"],
            max_pages=3,
            run_id="run-1",
        )
    )

    assert result.discovered_ids == ["101", "102"]
    assert result.new_ids == ["102"]
    assert result.artifact_refs["listing_crawl"].endswith("listing_crawl.json")


def test_crawl_listing_extracts_stepstone_inline_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_fetch(_self, url: str, timeout_seconds: float) -> FetchResult:
        if "page=1" in url:
            html = '<a href="/stellenangebote--Data-Scientist-Berlin-Test--13722274-inline.html">A</a>'
        else:
            html = ""
        return FetchResult(
            url=url,
            resolved_url=url,
            status_code=200,
            content=html,
            mode="http",
            warnings=[],
        )

    monkeypatch.setattr("src.core.scraping.service.HttpFetcher.fetch", fake_fetch)
    monkeypatch.setattr(
        "src.core.scraping.service.ScrapingArtifactStore.write_json",
        lambda _self, source, job_id, stage, filename, payload: (
            f"/tmp/{source}/{job_id}/{stage}/{filename}"
        ),
    )

    result = crawl_listing(
        CrawlListingRequest(
            source="stepstone",
            listing_url="https://www.stepstone.de/jobs/in-berlin",
            known_ids=[],
            max_pages=2,
            run_id="run-2",
        )
    )

    assert result.discovered_ids == ["13722274"]
    assert any("13722274-inline.html" in url for url in result.discovered_urls)
