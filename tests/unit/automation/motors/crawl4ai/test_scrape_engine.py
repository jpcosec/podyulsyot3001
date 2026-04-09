"""Tests for scraper artifact preservation behavior."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from crawl4ai.extraction_strategy import LLMExtractionStrategy

from src.automation.ariadne.models import (
    ApplicationRoutingInterpretation,
    JobPosting,
    ScrapePortalDefinition,
)
from src.automation.motors.crawl4ai.contracts import ScrapeDiscoveryEntry
from src.automation.motors.crawl4ai import scrape_engine as scrape_engine_module
from src.core.data_manager import DataManager
from src.automation.motors.crawl4ai.scrape_engine import (
    SmartScraperAdapter,
    _CompanyPortalAdapter,
    detect_language,
)


class _DummyAdapter(SmartScraperAdapter):
    def __init__(
        self,
        data_manager: DataManager | None = None,
        *,
        schema_cache_path: Path | None = None,
    ) -> None:
        super().__init__(data_manager)
        self._schema_cache_path = schema_cache_path

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

    @property
    def schema_cache_path(self) -> Path:
        if self._schema_cache_path is not None:
            return self._schema_cache_path
        return super().schema_cache_path


class _PortalDummyAdapter(_DummyAdapter):
    portal = ScrapePortalDefinition(
        source_name="dummy",
        base_url="https://aggregator.example.test",
        supported_params=[],
        job_id_pattern=r"-(\d+)$",
    )


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
    assert (ingest_dir / "raw.json").exists()
    assert (ingest_dir / "cleaned.json").exists()
    assert (ingest_dir / "extracted.json").exists()
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
    assert state_payload["application_method"] == "onsite"
    assert state_payload["application_url"] == detail_result.url
    assert state_payload["application_routing_diagnostics"]["review_required"] is True
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
    assert (failed_dir / "raw.json").exists()
    assert (failed_dir / "cleaned.json").exists()
    assert (failed_dir / "validation_error.json").exists()
    assert manager.has_ingested_job("dummy", "999") is False

    validation_error = manager.read_json_path(failed_dir / "validation_error.json")
    assert validation_error["job_id"] == "999"
    assert validation_error["has_valid_data"] is False


def test_extract_payload_uses_crawl4ai_llm_strategy_for_fallback(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("AUTOMATION_EXTRACTION_FALLBACKS", "llm")

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
    assert len(crawler.calls) >= 1
    called_url, rescue_config = crawler.calls[0]
    assert called_url == invalid_css_result.url
    assert isinstance(rescue_config.extraction_strategy, LLMExtractionStrategy)
    assert rescue_config.extraction_strategy.schema == JobPosting.model_json_schema()
    assert rescue_config.extraction_strategy.input_format == "markdown"


def test_extract_payload_enriches_routing_from_payload_without_llm(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)

    detail_result = _result(
        url="https://example.test/jobs/data-engineer-556",
        extracted_content=json.dumps(
            {
                "job_title": "Data Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
                "employment_type": "Full-time",
                "responsibilities": ["Build pipelines"],
                "requirements": ["Python"],
                "application_method": "Apply by email",
                "application_email": "mailto:jobs@example.test?subject=Data%20Engineer",
                "application_instructions": "Please send your CV to jobs@example.test.",
            }
        ),
        markdown="# Data Engineer\nPlease send your CV to jobs@example.test.",
        html="<html><body>detail</body></html>",
    )

    valid_data, _, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            detail_result,
            scraped_at=datetime.now(timezone.utc),
        )
    )

    assert extraction_error is None
    assert extraction_method == "css"
    assert valid_data is not None
    assert valid_data["application_method"] == "email"
    assert valid_data["application_email"] == "jobs@example.test"
    assert valid_data["application_url"] == detail_result.url
    assert valid_data["application_routing_diagnostics"]["used_llm"] is False


def test_extract_payload_uses_selective_llm_for_low_confidence_routing(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("AUTOMATION_EXTRACTION_FALLBACKS", "llm")

    detail_result = _result(
        url="https://example.test/jobs/data-engineer-557",
        extracted_content=json.dumps(
            {
                "job_title": "Data Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
                "employment_type": "Full-time",
                "responsibilities": ["Build pipelines"],
                "requirements": ["Python"],
            }
        ),
        markdown="# Data Engineer\nApply through our company portal.",
        html="<html><body>detail</body></html>",
    )

    class _FakeCrawler:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        async def arun(self, *, url: str, config):
            self.calls.append((url, config))
            return _result(
                url=url,
                extracted_content=json.dumps(
                    {
                        "application_method": "direct_url",
                        "application_url": "https://apply.example.test/jobs/557",
                        "application_instructions": "Apply in the employer portal.",
                    }
                ),
                markdown="",
                html="",
            )

    crawler = _FakeCrawler()
    valid_data, _, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            detail_result,
            crawler=crawler,
            scraped_at=datetime.now(timezone.utc),
        )
    )

    assert extraction_error is None
    assert extraction_method == "css"
    assert valid_data is not None
    assert valid_data["application_method"] == "direct_url"
    assert valid_data["application_url"] == "https://apply.example.test/jobs/557"
    assert valid_data["application_instructions"] == "Apply in the employer portal."
    assert valid_data["application_routing_confidence"] == 0.8
    assert valid_data["application_routing_diagnostics"]["used_llm"] is True
    assert len(crawler.calls) == 1
    _, rescue_config = crawler.calls[0]
    assert isinstance(rescue_config.extraction_strategy, LLMExtractionStrategy)
    assert (
        rescue_config.extraction_strategy.schema
        == ApplicationRoutingInterpretation.model_json_schema()
    )


def test_get_fast_schema_uses_representative_samples_and_filters_teaser_selectors(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    cache_path = tmp_path / "schemas" / "dummy_schema.json"
    adapter = _DummyAdapter(manager, schema_cache_path=cache_path)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    sample_payloads = {
        "https://example.test/jobs/data-engineer-1": "<body><main class='job'><h1>Job 1</h1><ul class='responsibilities'><li>Build</li></ul></main><section class='related-jobs'><h2>Related</h2></section></body>",
        "https://example.test/jobs/data-engineer-2": "<body><main class='job'><h1>Job 2</h1><ul class='responsibilities'><li>Scale</li></ul></main><section class='related-jobs'><h2>Related</h2></section></body>",
        "https://example.test/jobs/data-engineer-3": "<body><main class='job'><h1>Job 3</h1><ul class='responsibilities'><li>Ship</li></ul></main><section class='related-jobs'><h2>Related</h2></section></body>",
    }
    bad_schema = {
        "name": "Job Posting Detail",
        "baseSelector": "body",
        "fields": [
            {
                "name": "job_title",
                "selector": ".related-jobs h2",
                "type": "text",
            }
        ],
    }
    good_schema = {
        "name": "Job Posting Detail",
        "baseSelector": "main.job",
        "fields": [
            {"name": "job_title", "selector": "h1", "type": "text"},
            {
                "name": "responsibilities",
                "selector": ".responsibilities li",
                "type": "list",
                "fields": [{"name": "item", "selector": ".", "type": "text"}],
            },
        ],
    }

    class _FakeCrawler:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def arun(self, *, url: str, config):
            self.calls.append(url)
            return SimpleNamespace(
                url=url,
                success=True,
                cleaned_html=sample_payloads[url],
                error_message=None,
            )

    generated_htmls: list[str] = []

    def _fake_generate_schema(*, html: str, **kwargs):
        generated_htmls.append(html)
        if "Job 1" in html:
            return bad_schema
        return good_schema

    monkeypatch.setattr(
        scrape_engine_module.JsonCssExtractionStrategy,
        "generate_schema",
        staticmethod(_fake_generate_schema),
    )

    crawler = _FakeCrawler()
    schema = asyncio.run(
        adapter.get_fast_schema(
            crawler,
            "https://example.test/jobs/data-engineer-1",
            candidate_urls=list(sample_payloads),
        )
    )

    assert schema == good_schema
    assert crawler.calls == list(sample_payloads)
    assert len(generated_htmls) == 3
    assert json.loads(cache_path.read_text(encoding="utf-8")) == good_schema


def test_get_fast_schema_returns_none_when_all_generated_selectors_are_rejected(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    cache_path = tmp_path / "schemas" / "dummy_schema.json"
    adapter = _DummyAdapter(manager, schema_cache_path=cache_path)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    class _FakeCrawler:
        async def arun(self, *, url: str, config):
            return SimpleNamespace(
                url=url,
                success=True,
                cleaned_html="<body><main><h1>Job</h1></main><section class='related-jobs'><h2>Related</h2></section></body>",
                error_message=None,
            )

    monkeypatch.setattr(
        scrape_engine_module.JsonCssExtractionStrategy,
        "generate_schema",
        staticmethod(
            lambda **kwargs: {
                "name": "Job Posting Detail",
                "baseSelector": "body",
                "fields": [
                    {
                        "name": "job_title",
                        "selector": ".related-jobs h2",
                        "type": "text",
                    }
                ],
            }
        ),
    )

    schema = asyncio.run(
        adapter.get_fast_schema(
            _FakeCrawler(),
            "https://example.test/jobs/data-engineer-1",
            candidate_urls=["https://example.test/jobs/data-engineer-1"],
        )
    )

    assert schema is None
    assert cache_path.exists() is False


def test_company_portal_extract_links_filters_to_same_domain_job_urls(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _CompanyPortalAdapter(
        data_manager=manager,
        source_contract=scrape_engine_module.DiscoverySourceContract(
            kind="company_domain",
            source_name="company-boards.greenhouse.io",
            company_domain="boards.greenhouse.io",
            seed_url="https://boards.greenhouse.io/example/jobs/123",
            upstream_source="xing",
            upstream_job_id="123",
        ),
    )

    crawl_result = SimpleNamespace(
        links={
            "internal": [
                {
                    "href": "https://boards.greenhouse.io/example/jobs/321",
                    "text": "Senior Data Engineer",
                },
                {
                    "href": "https://boards.greenhouse.io/example/apply",
                    "text": "Apply now",
                },
            ],
            "external": [
                {
                    "href": "https://company.example.test/careers/openings/44",
                    "text": "Backend Engineer",
                }
            ],
        }
    )

    entries = adapter.extract_links(crawl_result)

    assert [entry.url for entry in entries] == [
        "https://boards.greenhouse.io/example/jobs/321"
    ]
    assert entries[0].source_contract is not None
    assert entries[0].source_contract.source_name == "company-boards.greenhouse.io"
    assert entries[0].source_metadata["upstream_source"] == "xing"


def test_run_cross_portal_discovery_seeds_company_domain_sources(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _PortalDummyAdapter(manager)
    manager.ingest_raw_job(
        source="dummy",
        job_id="123",
        payload={
            "job_title": "Data Engineer",
            "company_name": "Example Co",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Build pipelines"],
            "requirements": ["Python"],
            "application_method": "direct_url",
            "application_url": "https://boards.greenhouse.io/example/jobs/555",
        },
    )

    calls: list[tuple[str, list[str], list[str], int | None]] = []

    async def _fake_discover(self, crawler, *, seed_urls, already_scraped, limit):
        calls.append((self.source_name, seed_urls, already_scraped, limit))
        return ["job-555"]

    monkeypatch.setattr(
        _CompanyPortalAdapter,
        "discover_from_seed_urls",
        _fake_discover,
    )

    company_root = manager.source_root("company-boards.greenhouse.io")
    company_root.mkdir(parents=True, exist_ok=True)
    manager.ingest_raw_job(
        source="company-boards.greenhouse.io",
        job_id="already-there",
        payload={
            "job_title": "Existing",
            "company_name": "Example Co",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Build"],
            "requirements": ["Python"],
        },
    )

    discovered = asyncio.run(
        adapter._run_cross_portal_discovery(
            crawler=object(),
            ingested_job_ids=["123"],
            limit=5,
        )
    )

    assert discovered == ["job-555"]
    assert calls == [
        (
            "company-boards.greenhouse.io",
            ["https://boards.greenhouse.io/example/jobs/555"],
            ["already-there"],
            5,
        )
    ]


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


# ─── _normalize_payload tests ────────────────────────────────────────────────


def test_normalize_payload_unwraps_data_dict_wrapper(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    wrapped = {
        "data": {
            "job_title": "Data Engineer",
            "company_name": "Example Co",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Build pipelines"],
            "requirements": ["Python"],
        }
    }
    result = SimpleNamespace(
        url="https://example.test/jobs/1",
        extracted_content=json.dumps(wrapped),
        markdown=SimpleNamespace(fit_markdown="", raw_markdown=""),
        html="",
        cleaned_html="",
        error_message=None,
        crawl_stats={},
        status_code=200,
    )
    normalized = adapter._normalize_payload(wrapped, result=result)
    assert normalized is not None
    assert normalized["job_title"] == "Data Engineer"
    assert "data" not in normalized


def test_normalize_payload_unwraps_data_list_wrapper(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    wrapped = {
        "data": [
            {
                "job_title": "Data Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
                "employment_type": "Full-time",
                "responsibilities": ["Build pipelines"],
                "requirements": ["Python"],
            }
        ]
    }
    result = _result(
        url="https://example.test/jobs/2",
        extracted_content=json.dumps(wrapped),
        markdown="",
        html="",
    )
    normalized = adapter._normalize_payload(wrapped, result=result)
    assert normalized is not None
    assert normalized["job_title"] == "Data Engineer"
    assert "data" not in normalized


def test_normalize_payload_flattens_list_item_shapes(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": [{"item": "Build pipelines"}, {"item": "Deploy models"}],
        "requirements": [{"item": "Python"}, {"item": "SQL"}],
    }
    result = _result(
        url="https://example.test/jobs/3",
        extracted_content=json.dumps(payload),
        markdown="",
        html="",
    )
    normalized = adapter._normalize_payload(payload, result=result)
    assert normalized["responsibilities"] == ["Build pipelines", "Deploy models"]
    assert normalized["requirements"] == ["Python", "SQL"]


def test_normalize_payload_backfills_company_name_from_listing_case(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    payload = {
        "job_title": "Data Engineer",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Build pipelines"],
        "requirements": ["Python"],
    }
    listing_case = {
        "teaser_company": "BackfillCo",
        "teaser_location": "",
        "teaser_employment_type": "",
    }
    result = _result(
        url="https://example.test/jobs/4",
        extracted_content=json.dumps(payload),
        markdown="",
        html="",
    )
    normalized = adapter._normalize_payload(
        payload, result=result, listing_case=listing_case
    )
    assert normalized["company_name"] == "BackfillCo"


def test_normalize_payload_mines_bullets_from_german_markdown(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
    }
    markdown = (
        "# Data Engineer\n"
        "## Das erwartet Dich\n"
        "- Build production pipelines\n"
        "- Monitor model performance\n"
        "## Das bringst Du mit\n"
        "- 3+ years Python experience\n"
        "- SQL knowledge\n"
    )
    result = _result(
        url="https://example.test/jobs/5",
        extracted_content=json.dumps(payload),
        markdown=markdown,
        html="",
    )
    normalized = adapter._normalize_payload(payload, result=result)
    assert normalized["responsibilities"] == [
        "Build production pipelines",
        "Monitor model performance",
    ]
    assert normalized["requirements"] == ["3+ years Python experience", "SQL knowledge"]


def test_normalize_payload_does_not_overwrite_existing_valid_fields(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    payload = {
        "job_title": "Data Engineer",
        "company_name": "Original Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Original task"],
        "requirements": ["Original skill"],
    }
    listing_case = {
        "teaser_company": "BackfillCo",
        "teaser_location": "Munich",
        "teaser_employment_type": "Part-time",
    }
    result = _result(
        url="https://example.test/jobs/6",
        extracted_content=json.dumps(payload),
        markdown="## Das erwartet Dich\n- Mined task\n",
        html="",
    )
    normalized = adapter._normalize_payload(
        payload, result=result, listing_case=listing_case
    )
    assert normalized["company_name"] == "Original Co"
    assert normalized["responsibilities"] == ["Original task"]


def test_normalize_payload_returns_none_for_none_input(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    assert adapter._normalize_payload(None, result=None) is None


# ─── Integration: CSS extraction with wrapped payload becomes valid ─────────


def test_extract_payload_css_normalizes_wrapped_payload_to_valid(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)

    wrapped = {
        "data": {
            "job_title": "Data Engineer",
            "company_name": "Example Co",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Build pipelines"],
            "requirements": ["Python"],
        }
    }
    result = _result(
        url="https://example.test/jobs/789",
        extracted_content=json.dumps(wrapped),
        markdown="# Data Engineer",
        html="<html><body>detail</body></html>",
    )

    valid_data, merged_payload, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(result, scraped_at=datetime.now(timezone.utc))
    )

    assert extraction_error is None
    assert extraction_method == "css"
    assert valid_data is not None
    assert valid_data["job_title"] == "Data Engineer"


def test_extract_payload_css_normalizes_item_shapes_to_valid(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)

    payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": [{"item": "Build pipelines"}, {"item": "Deploy models"}],
        "requirements": [{"item": "Python"}],
    }
    result = _result(
        url="https://example.test/jobs/790",
        extracted_content=json.dumps(payload),
        markdown="# Data Engineer",
        html="<html><body>detail</body></html>",
    )

    valid_data, merged_payload, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(result, scraped_at=datetime.now(timezone.utc))
    )

    assert extraction_error is None
    assert valid_data is not None
    assert valid_data["responsibilities"] == ["Build pipelines", "Deploy models"]
    assert valid_data["requirements"] == ["Python"]


def test_extract_payload_css_backfills_missing_company_from_listing_case(
    tmp_path,
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)

    payload = {
        "job_title": "Data Engineer",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Build pipelines"],
        "requirements": ["Python"],
    }
    from src.automation.motors.crawl4ai.contracts import (
        DiscoveryListingData,
        ScrapeDiscoveryEntry,
    )

    discovery_entry = ScrapeDiscoveryEntry(
        url="https://example.test/jobs/791",
        job_id="791",
        listing_position=0,
        listing_data=DiscoveryListingData(
            job_title="Data Engineer",
            company_name="Listed Co",
            location="Berlin",
            employment_type="Full-time",
            posted_date="vor 2 Tagen",
        ),
    )

    result = _result(
        url="https://example.test/jobs/791",
        extracted_content=json.dumps(payload),
        markdown="# Data Engineer",
        html="<html><body>detail</body></html>",
    )

    valid_data, merged_payload, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            result,
            discovery_entry=discovery_entry,
            scraped_at=datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc),
        )
    )

    assert extraction_error is None
    assert valid_data is not None
    assert valid_data["company_name"] == "Listed Co"


def test_extract_payload_prefers_browseros_fallback_before_llm(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    monkeypatch.setenv("AUTOMATION_EXTRACTION_FALLBACKS", "browseros,llm")

    async def _fake_browseros_rescue(url: str, markdown_content: str):
        return (
            {
                "job_title": "BrowserOS Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
                "employment_type": "Full-time",
                "responsibilities": ["Inspect DOM semantically"],
                "requirements": ["Browser automation"],
            },
            None,
        )

    async def _fake_llm_rescue(crawler, url: str, markdown_content: str):
        raise AssertionError("LLM rescue should be skipped when BrowserOS succeeds")

    monkeypatch.setattr(adapter, "_browseros_rescue", _fake_browseros_rescue)
    monkeypatch.setattr(adapter, "_llm_rescue", _fake_llm_rescue)

    invalid_css_result = _result(
        url="https://example.test/jobs/browseros-801",
        extracted_content=json.dumps(
            {
                "job_title": "Incomplete",
                "company_name": "Example Co",
                "location": "Berlin",
            }
        ),
        markdown="# BrowserOS Engineer",
        html="<html><body>detail</body></html>",
    )

    valid_data, _, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            invalid_css_result,
            scraped_at=datetime.now(timezone.utc),
        )
    )

    assert extraction_error is None
    assert extraction_method == "browseros"
    assert valid_data is not None
    assert valid_data["job_title"] == "BrowserOS Engineer"


def test_browseros_rescue_uses_mcp_page_content(tmp_path, monkeypatch) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)

    class _FakeBrowserOSClient:
        def __init__(self) -> None:
            self.closed_pages: list[int] = []

        def new_hidden_page(self, url: str = "about:blank") -> int:
            return 77

        def navigate(self, url: str, page_id: int) -> None:
            return None

        def get_page_content(self, page_id: int) -> dict:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "# Data Engineer\n## Das erwartet Dich\n- Build pipelines\n## Das bringst Du mit\n- Python\n",
                    }
                ]
            }

        def close_page(self, page_id: int) -> None:
            self.closed_pages.append(page_id)

    monkeypatch.setitem(
        sys.modules,
        "src.automation.motors.browseros.cli.client",
        SimpleNamespace(BrowserOSClient=_FakeBrowserOSClient),
    )

    payload, error = asyncio.run(
        adapter._browseros_rescue("https://example.test/jobs/900", "")
    )

    assert error is None
    assert payload is not None
    assert payload["job_title"] == "Data Engineer"
    assert payload["responsibilities"] == ["Build pipelines"]
    assert payload["requirements"] == ["Python"]


def test_mine_bullets_from_markdown_supports_bold_section_headings(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))

    bullets = adapter._mine_bullets_from_markdown(
        "**Die Stelle im Überblick**\n- Analyze data\n**Danach suchen wir**\n- Python\n"
    )

    assert bullets["responsibilities"] == ["Analyze data"]
    assert bullets["requirements"] == ["Python"]


def test_mine_bullets_from_markdown_supports_prose_sections(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))

    bullets = adapter._mine_bullets_from_markdown(
        "## Your responsibility\n"
        "Conduct animal experiments and write scientific manuscripts.\n"
        "## Your profile\n"
        "- Biology degree\n"
    )

    assert bullets["responsibilities"] == [
        "Conduct animal experiments and write scientific manuscripts."
    ]
    assert bullets["requirements"] == ["Biology degree"]


def test_normalize_payload_recovers_hero_scalars_and_cleans_location(tmp_path) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    result = _result(
        url="https://example.test/jobs/stepstone-1",
        extracted_content="{}",
        markdown=(
            "# Data Scientist\n"
            "* Example Research GmbH\n"
            "* [Berlin](https://example.test/location)\n"
            "* Homeoffice moglich, Vollzeit\n"
        ),
        html="<html></html>",
    )

    payload = adapter._normalize_payload(
        {"job_title": "Data Scientist", "location": "Berlin + 0 more"},
        result=result,
        listing_case=None,
    )

    assert payload is not None
    assert payload["company_name"] == "Example Research GmbH"
    assert payload["location"] == "Berlin"
    assert payload["employment_type"] == "Full-time"


def test_normalize_payload_extracts_company_name_from_inline_markdown_link(
    tmp_path,
) -> None:
    adapter = _DummyAdapter(DataManager(tmp_path / "data" / "jobs"))
    result = _result(
        url="https://example.test/jobs/stepstone-2",
        extracted_content="{}",
        markdown=(
            "# Data Scientist\n"
            "**Data Scientist**[ InGef - Institut fur angewandte Gesundheitsforschung Berlin GmbH](https://example.test/company)\n"
        ),
        html="<html></html>",
    )

    payload = adapter._normalize_payload(
        {"job_title": "Data Scientist"},
        result=result,
        listing_case=None,
    )

    assert payload is not None
    assert (
        payload["company_name"]
        == "InGef - Institut fur angewandte Gesundheitsforschung Berlin GmbH"
    )


def test_extract_payload_merges_css_scalars_with_browseros_lists(
    tmp_path, monkeypatch
) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    monkeypatch.setenv("AUTOMATION_EXTRACTION_FALLBACKS", "browseros")

    async def _fake_browseros_rescue(url: str, markdown_content: str):
        return (
            {
                "responsibilities": ["Build pipelines"],
                "requirements": ["Python"],
                "employment_type": "Full-time",
            },
            None,
        )

    monkeypatch.setattr(adapter, "_browseros_rescue", _fake_browseros_rescue)

    invalid_css_result = _result(
        url="https://example.test/jobs/merge-901",
        extracted_content=json.dumps(
            {
                "job_title": "Data Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
            }
        ),
        markdown="# Data Engineer",
        html="<html><body>detail</body></html>",
    )

    valid_data, _, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            invalid_css_result,
            scraped_at=datetime.now(timezone.utc),
        )
    )

    assert extraction_error is None
    assert extraction_method == "browseros"
    assert valid_data is not None
    assert valid_data["company_name"] == "Example Co"
    assert valid_data["location"] == "Berlin"
    assert valid_data["responsibilities"] == ["Build pipelines"]


# ─── Transient error retry tests ───────────────────────────────────────────────


def test_retry_crawl_succeeds_on_first_attempt(tmp_path) -> None:
    """If crawl succeeds on first try, no retries are performed."""
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)

    success_result = SimpleNamespace(
        url="https://example.test/jobs/retry-1",
        success=True,
        extracted_content=json.dumps(
            {
                "job_title": "Data Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
                "employment_type": "Full-time",
                "responsibilities": ["Build pipelines"],
                "requirements": ["Python"],
            }
        ),
        markdown=SimpleNamespace(fit_markdown="", raw_markdown=""),
        html="<html><body>detail</body></html>",
        cleaned_html="<html><body>detail</body></html>",
        error_message=None,
        crawl_stats={},
        status_code=200,
    )

    class _FakeCrawler:
        def __init__(self):
            self.call_count = 0

        async def arun(self, *, url: str, config):
            self.call_count += 1
            return success_result

        async def sleep(self, seconds):
            pass

    crawler = _FakeCrawler()
    result = asyncio.run(
        adapter._retry_crawl(
            crawler,
            "https://example.test/jobs/retry-1",
            _DummyAdapter(manager).get_base_crawl_config(),
        )
    )
    assert result is success_result
    assert crawler.call_count == 1


def test_retry_crawl_retries_on_transient_error(tmp_path) -> None:
    """Transient errors trigger retry up to max_retries."""
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    run_config = adapter.get_base_crawl_config()

    transient_result = SimpleNamespace(
        url="https://example.test/jobs/retry-2",
        success=False,
        error_message="net::ERR_NETWORK_CHANGED",
        extracted_content="",
        markdown=None,
        html="",
        cleaned_html="",
        crawl_stats={},
        status_code=0,
    )
    success_result = SimpleNamespace(
        url="https://example.test/jobs/retry-2",
        success=True,
        extracted_content=json.dumps(
            {
                "job_title": "Data Engineer",
                "company_name": "Example Co",
                "location": "Berlin",
                "employment_type": "Full-time",
                "responsibilities": ["Build pipelines"],
                "requirements": ["Python"],
            }
        ),
        markdown=SimpleNamespace(fit_markdown="", raw_markdown=""),
        html="<html><body>detail</body></html>",
        cleaned_html="<html><body>detail</body></html>",
        error_message=None,
        crawl_stats={},
        status_code=200,
    )

    class _FakeCrawler:
        def __init__(self):
            self.call_count = 0
            self.sleep_calls: list[int] = []

        async def arun(self, *, url: str, config):
            self.call_count += 1
            if self.call_count <= 2:
                return transient_result
            return success_result

        async def sleep(self, seconds):
            self.sleep_calls.append(seconds)

    crawler = _FakeCrawler()
    result = asyncio.run(
        adapter._retry_crawl(crawler, "https://example.test/jobs/retry-2", run_config)
    )
    assert result is success_result
    assert crawler.call_count == 3
    assert crawler.sleep_calls == [1, 2]


def test_retry_crawl_gives_up_after_max_retries(tmp_path) -> None:
    """After max_retries attempts, the last result is returned."""
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    run_config = adapter.get_base_crawl_config()

    transient_result = SimpleNamespace(
        url="https://example.test/jobs/retry-3",
        success=False,
        error_message="net::ERR_NETWORK_CHANGED",
        extracted_content="",
        markdown=None,
        html="",
        cleaned_html="",
        crawl_stats={},
        status_code=0,
    )

    class _FakeCrawler:
        def __init__(self):
            self.call_count = 0

        async def arun(self, *, url: str, config):
            self.call_count += 1
            return transient_result

        async def sleep(self, seconds):
            pass

    crawler = _FakeCrawler()
    result = asyncio.run(
        adapter._retry_crawl(
            crawler, "https://example.test/jobs/retry-3", run_config, max_retries=2
        )
    )
    assert result is transient_result
    assert crawler.call_count == 3


def test_retry_crawl_does_not_retry_non_transient_errors(tmp_path) -> None:
    """Non-transient errors fail immediately without retry."""
    manager = DataManager(tmp_path / "data" / "jobs")
    adapter = _DummyAdapter(manager)
    run_config = adapter.get_base_crawl_config()

    permanent_result = SimpleNamespace(
        url="https://example.test/jobs/retry-4",
        success=False,
        error_message="net::ERR_FILE_NOT_FOUND",
        extracted_content="",
        markdown=None,
        html="",
        cleaned_html="",
        crawl_stats={},
        status_code=404,
    )

    class _FakeCrawler:
        def __init__(self):
            self.call_count = 0

        async def arun(self, *, url: str, config):
            self.call_count += 1
            return permanent_result

        async def sleep(self, seconds):
            pass

    crawler = _FakeCrawler()
    result = asyncio.run(
        adapter._retry_crawl(crawler, "https://example.test/jobs/retry-4", run_config)
    )
    assert result is permanent_result
    assert crawler.call_count == 1
