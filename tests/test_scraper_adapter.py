"""Tests for scraper artifact preservation behavior."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from src.core.data_manager import DataManager
from src.scraper.smart_adapter import SmartScraperAdapter


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
                detail_result.url: {
                    "url": detail_result.url,
                    "search_url": listing_result.url,
                    "listing_position": 0,
                    "listing_data": {"posted_date": "vor 2 Tagen"},
                    "listing_link": {"href": detail_result.url},
                }
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

    listing_payload = json.loads((ingest_dir / "listing.json").read_text())
    assert listing_payload["listing_data"]["posted_date"] == "vor 2 Tagen"
    state_payload = json.loads((ingest_dir / "state.json").read_text())
    assert state_payload["listing_case"]["listed_at_relative"] == "vor 2 Tagen"
    assert (
        state_payload["posted_date"] == state_payload["listing_case"]["listed_at_iso"]
    )


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
