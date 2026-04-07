"""Tests for scraper artifact preservation behavior."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

from crawl4ai.extraction_strategy import LLMExtractionStrategy

from src.automation.ariadne.models import JobPosting
from src.automation.motors.crawl4ai.contracts import ScrapeDiscoveryEntry
from src.core.data_manager import DataManager
from src.automation.motors.crawl4ai.scrape_engine import (
    SmartScraperAdapter,
    detect_language,
)


class _DummyAdapter(SmartScraperAdapter):
    @property
    def source_name(self) -> str:
        return "dummy"

    @property
    def supported_params(self) -> list[str]:
        return []

    def get_search_url(self, **kwargs) -> str:
        return "https://example.test/search"

    def extract_job_id(self, url: str) -> str:
        return url.rsplit("-", 1)[-1]

    def extract_links(self, crawl_result):
        return []

    def get_llm_instructions(self) -> str:
        return ""


def _result(*, url: str, extracted_content: str, markdown: str, html: str):
    return SimpleNamespace(
        url=url,
        success=True,
        extracted_content=extracted_content,
        markdown=SimpleNamespace(fit_markdown=markdown, raw_markdown=markdown),
        html=html,
        cleaned_html=html,
        error_message=None,
        crawl_stats={},
        status_code=200,
    )


def test_process_results_persists_listing_and_raw_artifacts(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Build pipelines"],
        "requirements": ["Python"],
        "posted_date": "vor 2 Tagen",
    }
    detail_result = _result(
        url="https://example.test/jobs/data-engineer-123",
        extracted_content=json.dumps(payload),
        markdown="# Data Engineer",
        html="<html><body>detail</body></html>",
    )
    listing_result = _result(
        url="https://example.test/search?q=data",
        extracted_content="",
        markdown="listing markdown",
        html="<html><body>listing</body></html>",
    )

    asyncio.run(
        adapter._process_results(
            results=[detail_result],
            discovery_entries={
                detail_result.url: ScrapeDiscoveryEntry(
                    url=detail_result.url,
                    job_id="123",
                    search_url=listing_result.url,
                    listing_position=0,
                    listing_snippet="Data Engineer teaser",
                    listing_data={"posted_date": "vor 2 Tagen"},
                    listing_link={"href": detail_result.url},
                    source_metadata={"card_variant": "default"},
                )
            },
            listing_result=listing_result,
        )
    )

    job_id = "123"
    ingest_dir = manager.node_stage_dir("dummy", job_id, "ingest", "proposed")
    assert (ingest_dir / "state.json").exists()
    assert (ingest_dir / "content.md").exists()
    assert (ingest_dir / "raw_page.html").exists()
    assert (ingest_dir / "cleaned_page.html").exists()
    assert (ingest_dir / "raw_extracted.json").exists()
    assert (ingest_dir / "listing.json").exists()
    assert (ingest_dir / "listing_content.md").exists()
    assert (ingest_dir / "listing_page.html").exists()
    assert (ingest_dir / "listing_page.cleaned.html").exists()

    listing_payload = manager.read_json_path(ingest_dir / "listing.json")
    assert listing_payload["job_id"] == "123"
    assert listing_payload["listing_data"]["posted_date"] == "vor 2 Tagen"
    assert listing_payload["source_metadata"]["card_variant"] == "default"
    state_payload = manager.read_json_path(ingest_dir / "state.json")
    assert state_payload["listing_case"]["listed_at_relative"] == "vor 2 Tagen"
    assert (
        state_payload["posted_date"] == state_payload["listing_case"]["listed_at_iso"]
    )
    listing_case_payload = manager.read_json_path(ingest_dir / "listing_case.json")
    assert listing_case_payload["job_id"] == "123"
    assert listing_case_payload["source_metadata"]["card_variant"] == "default"


def test_process_results_fails_closed_but_persists_failed_artifacts(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    invalid_payload = {
        "job_title": "Incomplete",
        "company_name": "Example Co",
        "location": "Berlin",
    }
    detail_result = _result(
        url="https://example.test/jobs/incomplete-999",
        extracted_content=json.dumps(invalid_payload),
        markdown="# Incomplete",
        html="<html><body>detail</body></html>",
    )

    ingested = asyncio.run(adapter._process_results(results=[detail_result]))

    assert ingested == []
    failed_dir = manager.node_stage_dir("dummy", "999", "ingest", "failed")
    assert (failed_dir / "state.json").exists()
    assert (failed_dir / "raw_page.html").exists()
    assert manager.has_ingested_job("dummy", "999") is False


def test_extract_payload_uses_crawl4ai_llm_strategy_for_fallback(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    invalid_css_result = _result(
        url="https://example.test/jobs/data-engineer-555",
        extracted_content=json.dumps(
            {
                "job_title": "Incomplete",
                "company_name": "Example Co",
                "location": "Berlin",
            }
        ),
        markdown="# Data Engineer\nBuild pipelines with Python.",
        html="<html><body>detail</body></html>",
    )
    llm_payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Build pipelines"],
        "requirements": ["Python"],
    }

    class _FakeCrawler:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        async def arun(self, *, url: str, config):
            self.calls.append((url, config))
            return _result(
                url=url,
                extracted_content=json.dumps(llm_payload),
                markdown="",
                html="",
            )

    crawler = _FakeCrawler()

    valid_data, merged_payload, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            invalid_css_result,
            crawler=crawler,
            scraped_at=datetime.now(timezone.utc),
        )
    )

    assert extraction_error is None
    assert extraction_method == "llm"
    assert valid_data is not None
    assert merged_payload is not None
    assert valid_data["job_title"] == "Data Engineer"
    assert len(crawler.calls) == 1
    called_url, rescue_config = crawler.calls[0]
    assert called_url == invalid_css_result.url
    assert isinstance(rescue_config.extraction_strategy, LLMExtractionStrategy)
    assert rescue_config.extraction_strategy.schema == JobPosting.model_json_schema()
    assert rescue_config.extraction_strategy.input_format == "markdown"


def test_detect_language_handles_short_english_titles() -> None:
    assert detect_language("Data Engineer Berlin") == "en"


def test_detect_language_handles_mixed_language_postings() -> None:
    text = (
        "Data Engineer gesucht. Build pipelines with Python and SQL. Standort Berlin."
    )

    assert detect_language(text) == "en"


def test_process_results_adds_detected_original_language(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Build pipelines"],
        "requirements": ["Python"],
    }
    detail_result = _result(
        url="https://example.test/jobs/data-engineer-124",
        extracted_content=json.dumps(payload),
        markdown="Data Engineer gesucht. Build pipelines with Python and SQL.",
        html="<html><body>detail</body></html>",
    )

    asyncio.run(adapter._process_results(results=[detail_result]))

    state_payload = manager.read_json_path(
        manager.node_stage_dir("dummy", "124", "ingest", "proposed") / "state.json"
    )
    assert state_payload["original_language"] == "en"
