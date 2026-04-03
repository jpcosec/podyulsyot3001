"""Shared scraper base for canonical job ingestion."""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
    RateLimiter,
    SemaphoreDispatcher,
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from dotenv import load_dotenv

from src.core.data_manager import DataManager
from src.scraper.models import JobPosting
from src.shared.log_tags import LogTag

load_dotenv()

logger = logging.getLogger(__name__)


DiscoveryEntry = dict[str, Any]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_relative_date(
    value: str | None, *, scraped_at: datetime
) -> tuple[str | None, str | None]:
    """Normalize relative listing dates to ISO-8601 when possible."""
    if not value:
        return None, None

    text = " ".join(value.split()).strip()
    lowered = text.lower()

    embedded_patterns = [
        r"\d+\s+minute[s]?\s+ago",
        r"\d+\s+hour[s]?\s+ago",
        r"\d+\s+day[s]?\s+ago",
        r"\d+\s+week[s]?\s+ago",
        r"\d+\s+month[s]?\s+ago",
        r"vor\s+\d+\s+minute[n]?",
        r"vor\s+\d+\s+stunde[n]?",
        r"vor\s+\d+\s+tag(?:en)?",
        r"vor\s+\d+\s+woche[n]?",
        r"vor\s+\d+\s+monat(?:en)?",
        r"yesterday",
        r"today",
        r"gestern",
        r"heute",
    ]
    for pattern in embedded_patterns:
        match = re.search(pattern, lowered)
        if match:
            lowered = match.group(0)
            text = text[match.start() : match.end()]
            break

    if lowered in {"yesterday", "gestern"}:
        return text, (scraped_at - timedelta(days=1)).isoformat()
    if lowered in {"today", "heute"}:
        return text, scraped_at.isoformat()

    patterns = [
        (r"^(\d+)\s+minute[s]?\s+ago$", "minutes"),
        (r"^(\d+)\s+hour[s]?\s+ago$", "hours"),
        (r"^(\d+)\s+day[s]?\s+ago$", "days"),
        (r"^(\d+)\s+week[s]?\s+ago$", "weeks"),
        (r"^(\d+)\s+month[s]?\s+ago$", "months"),
        (r"^vor\s+(\d+)\s+minute[n]?$", "minutes"),
        (r"^vor\s+(\d+)\s+stunde[n]?$", "hours"),
        (r"^vor\s+(\d+)\s+tag(en)?$", "days"),
        (r"^vor\s+(\d+)\s+woche[n]?$", "weeks"),
        (r"^vor\s+(\d+)\s+monat(en)?$", "months"),
    ]

    for pattern, unit in patterns:
        match = re.match(pattern, lowered)
        if not match:
            continue
        amount = int(match.group(1))
        if unit == "minutes":
            delta = timedelta(minutes=amount)
        elif unit == "hours":
            delta = timedelta(hours=amount)
        elif unit == "days":
            delta = timedelta(days=amount)
        elif unit == "weeks":
            delta = timedelta(weeks=amount)
        else:
            delta = timedelta(days=30 * amount)
        return text, (scraped_at - delta).isoformat()

    return text, None


# TODO(future): detect_language is a naive heuristic, fails on short/mixed-language postings — see future_docs/issues/scraper_fragility.md
def detect_language(markdown_text: str) -> str:
    """Naive fallback to detect if a text is German or English."""
    german_markers = [
        " und ",
        " wie ",
        " wir ",
        " für ",
        " sind ",
        " werden ",
        "aufgabengebiet",
        "tätigkeit",
        "erfahrung",
        "deutsch",
    ]
    lowered = markdown_text.lower()
    marker_hits = sum(lowered.count(marker) for marker in german_markers)
    has_umlaut = any(ch in markdown_text for ch in "äöüß")
    if marker_hits >= 2 or has_umlaut:
        return "de"
    return "en"


class SmartScraperAdapter(ABC):
    """Base class for canonical source discovery and single-job ingestion."""

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Portal source identifier."""

    @property
    @abstractmethod
    def supported_params(self) -> list[str]:
        """CLI filter names supported by this provider."""

    @abstractmethod
    def get_search_url(self, **kwargs) -> str:
        """Build the listing URL for discovery."""

    @abstractmethod
    def extract_job_id(self, url: str) -> str:
        """Extract a stable job identifier from a posting URL."""

    @abstractmethod
    def extract_links(self, crawl_result: Any) -> list[str]:
        """Return discovery entries from a listing result.

        Implementations may return plain URL strings or dictionaries containing
        at least ``url`` plus any listing-side metadata worth preserving.
        """

    @abstractmethod
    def get_llm_instructions(self) -> str:
        """Return portal-specific extraction hints."""

    def get_llm_config(self) -> LLMConfig:
        """Return the default LLM configuration for rescue extraction.

        Returns:
            The configured LLM settings for provider fallback extraction.
        """
        return LLMConfig(
            provider="gemini/gemini-2.5-flash",
            api_token=os.environ.get("GOOGLE_API_KEY", ""),
            temperature=0.1,
        )

    def _has_llm_key(self) -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY"))

    def get_browser_config(self) -> BrowserConfig:
        """Return the default browser configuration for scraping runs.

        Returns:
            Browser settings tuned for text-first ingestion.
        """
        return BrowserConfig(headless=True, text_mode=True)

    def get_base_crawl_config(self) -> CrawlerRunConfig:
        """Return the shared Crawl4AI run configuration.

        Returns:
            Crawl settings reused for listing and detail page retrieval.
        """
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            simulate_user=True,
            magic=True,
            override_navigator=True,
            word_count_threshold=10,
            exclude_external_images=True,
            exclude_external_links=False,
            excluded_tags=["nav", "footer", "script", "style", "aside"],
        )

    def get_dispatcher(self) -> SemaphoreDispatcher:
        """Return the dispatcher used to bound concurrent crawl sessions.

        Returns:
            A dispatcher with the default rate-limiting policy.
        """
        return SemaphoreDispatcher(
            max_session_permit=5,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 3.0),
                max_retries=2,
                rate_limit_codes=[429, 503],
            ),
        )

    @property
    def schema_cache_path(self) -> Path:
        """Return the path used to cache the generated CSS extraction schema."""
        return Path(
            f"./data/ariadne/assets/crawl4ai_schemas/{self.source_name}_schema.json"
        )

    def get_schema_generation_hints(self) -> str:
        """Provider-specific hints for CSS schema generation."""
        return ""

    def _schema_generation_query(self) -> str:
        base_rules = [
            f"Generate CSS selectors for the main {self.source_name} job detail page only.",
            "Return a Crawl4AI CSS extraction schema, not a JSON Schema document.",
            "The output must use the exact top-level shape: {name, baseSelector, fields}.",
            "Each field entry must use {name, selector, type}; list fields must also include nested {fields} entries.",
            "Map exactly to the target extraction contract and do not add extra fields.",
            "Extract only the primary job posting, never related jobs, similar jobs, recommendations, teasers, carousels, sticky headers, or footer cards.",
            "Prefer selectors scoped to the detail page's main content container.",
            "If the page repeats the same information in multiple layouts, choose the selector that belongs to the primary detail content.",
            "Do not source missing fields from nearby teaser cards or listing modules.",
            "For list fields, extract only the actual bullet items for the main posting.",
            "If a field cannot be found on the main detail page, leave it unmapped rather than using unrelated content.",
        ]
        provider_hints = self.get_schema_generation_hints().strip()
        if provider_hints:
            base_rules.append(provider_hints)
        return " ".join(base_rules)

    def _css_schema_target_example(self) -> dict[str, Any]:
        return {
            "name": "Job Posting Detail",
            "baseSelector": "body",
            "fields": [
                {"name": "job_title", "selector": "h1", "type": "text"},
                {"name": "company_name", "selector": ".company", "type": "text"},
                {"name": "location", "selector": ".location", "type": "text"},
                {
                    "name": "employment_type",
                    "selector": ".employment-type",
                    "type": "text",
                },
                {"name": "posted_date", "selector": ".posted-date", "type": "text"},
                {
                    "name": "responsibilities",
                    "selector": ".responsibilities li",
                    "type": "list",
                    "fields": [{"name": "item", "selector": ".", "type": "text"}],
                },
                {
                    "name": "requirements",
                    "selector": ".requirements li",
                    "type": "list",
                    "fields": [{"name": "item", "selector": ".", "type": "text"}],
                },
                {"name": "salary", "selector": ".salary", "type": "text"},
                {
                    "name": "remote_policy",
                    "selector": ".remote-policy",
                    "type": "text",
                },
                {
                    "name": "benefits",
                    "selector": ".benefits li",
                    "type": "list",
                    "fields": [{"name": "item", "selector": ".", "type": "text"}],
                },
                {
                    "name": "company_description",
                    "selector": ".company-description",
                    "type": "text",
                },
                {
                    "name": "company_industry",
                    "selector": ".company-industry",
                    "type": "text",
                },
                {
                    "name": "company_size",
                    "selector": ".company-size",
                    "type": "text",
                },
                {
                    "name": "application_deadline",
                    "selector": ".application-deadline",
                    "type": "text",
                },
                {
                    "name": "application_method",
                    "selector": ".application-method",
                    "type": "text",
                },
                {
                    "name": "application_url",
                    "selector": ".apply-link",
                    "type": "attribute",
                    "attribute": "href",
                },
                {
                    "name": "application_email",
                    "selector": "a[href^='mailto:']",
                    "type": "attribute",
                    "attribute": "href",
                },
                {
                    "name": "application_instructions",
                    "selector": ".application-instructions",
                    "type": "text",
                },
                {
                    "name": "reference_number",
                    "selector": ".reference-number",
                    "type": "text",
                },
                {
                    "name": "contact_info",
                    "selector": ".contact-info",
                    "type": "text",
                },
            ],
        }

    async def get_fast_schema(
        self, crawler: AsyncWebCrawler, sample_url: str
    ) -> dict | None:
        """Return cached CSS schema or generate it using the LLM."""
        if self.schema_cache_path.exists():
            logger.info("%s Using cached CSS schema.", LogTag.CACHE)
            return json.loads(self.schema_cache_path.read_text(encoding="utf-8"))

        if not self._has_llm_key():
            logger.warning(
                "%s No API key; skipping CSS schema generation.", LogTag.WARN
            )
            return None

        logger.info("%s Learning page structure for %s", LogTag.LLM, self.source_name)
        sample_result = await crawler.arun(
            url=sample_url, config=self.get_base_crawl_config()
        )
        if not sample_result.success:
            logger.error("%s Could not download sample page.", LogTag.FAIL)
            return None

        try:
            schema = JsonCssExtractionStrategy.generate_schema(
                html=sample_result.cleaned_html[:50000],
                schema_type="CSS",
                target_json_example=json.dumps(
                    self._css_schema_target_example(), indent=2
                ),
                query=self._schema_generation_query(),
                llm_config=self.get_llm_config(),
            )
            self.schema_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.schema_cache_path.write_text(
                json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info("%s CSS schema generated and cached.", LogTag.OK)
            return schema
        except Exception as exc:
            logger.error("%s Error generating schema: %s", LogTag.FAIL, exc)
            return None

    def _parse_payload(self, raw_content: str) -> tuple[dict | None, str | None]:
        """Parse extractor output into a dictionary payload when possible."""
        try:
            raw_data = json.loads(raw_content)
            raw_data = (
                raw_data[0] if isinstance(raw_data, list) and raw_data else raw_data
            )
            if isinstance(raw_data, dict):
                return raw_data, None
            return None, "Extracted content is not a valid JSON dictionary."
        except Exception as exc:
            return None, str(exc)

    def _validate_payload(self, payload: dict | None) -> tuple[dict | None, str | None]:
        """Validate a merged payload against the job posting contract."""
        if not payload:
            return None, "No payload to validate."
        try:
            return JobPosting(**payload).model_dump(), None
        except Exception as exc:
            return None, str(exc)

    async def _llm_rescue(
        self, markdown_content: str
    ) -> tuple[dict | None, str | None]:
        """Use the LLM to extract structured data from markdown content."""
        if not self._has_llm_key() or not markdown_content:
            return None, "No LLM API key or empty markdown content."

        logger.info("%s LLM rescue for %s", LogTag.FALLBACK, self.source_name)
        try:
            import litellm

            prompt = (
                f"{self.get_llm_instructions()}\n\n"
                "Extract the following JSON schema from the text below. "
                "Return ONLY valid JSON, no markdown fences.\n\n"
                f"Schema:\n{json.dumps(JobPosting.model_json_schema(), indent=2)}\n\n"
                f"Text:\n{markdown_content[:8000]}"
            )
            llm_cfg = self.get_llm_config()
            response = await litellm.acompletion(
                model=llm_cfg.provider,
                messages=[{"role": "user", "content": prompt}],
                api_key=llm_cfg.api_token,
                temperature=llm_cfg.temperature or 0.1,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                if content.endswith("```"):
                    content = content[:-3].strip()
            return self._parse_payload(content)
        except Exception as exc:
            logger.error("%s LLM rescue error: %s", LogTag.FAIL, exc)
            return None, f"LLM exception: {exc}"

    def _listing_case_payload(
        self,
        *,
        discovery_entry: DiscoveryEntry | None,
        scraped_at: datetime,
    ) -> dict[str, Any] | None:
        if not discovery_entry:
            return None
        listing_data = dict(discovery_entry.get("listing_data", {}))
        listed_at_relative, listed_at_iso = normalize_relative_date(
            listing_data.get("posted_date"),
            scraped_at=scraped_at,
        )
        return {
            "job_id": self.extract_job_id(discovery_entry["url"]),
            "url": discovery_entry["url"],
            "search_url": discovery_entry.get("search_url"),
            "listing_position": discovery_entry.get("listing_position"),
            "scraped_at": scraped_at.isoformat(),
            "listed_at_relative": listed_at_relative,
            "listed_at_iso": listed_at_iso,
            "teaser_title": listing_data.get("job_title"),
            "teaser_company": listing_data.get("company_name"),
            "teaser_location": listing_data.get("location"),
            "teaser_salary": listing_data.get("salary"),
            "teaser_employment_type": listing_data.get("employment_type"),
            "teaser_text": discovery_entry.get("listing_snippet"),
        }

    def _merge_listing_into_payload(
        self,
        *,
        payload: dict | None,
        listing_case: dict[str, Any] | None,
    ) -> dict | None:
        if payload is None and listing_case is None:
            return None
        merged = dict(payload or {})
        if listing_case:
            merged["listing_case"] = listing_case
            if listing_case.get("listed_at_relative") and not merged.get("days_ago"):
                merged["days_ago"] = listing_case["listed_at_relative"]
            if listing_case.get("listed_at_iso"):
                merged["posted_date"] = listing_case["listed_at_iso"]
        return merged

    def _markdown_text(self, result: Any) -> str:
        if not result.markdown:
            return ""
        return (
            getattr(result.markdown, "fit_markdown", None)
            or getattr(result.markdown, "raw_markdown", None)
            or str(result.markdown)
        )

    def _normalize_discovery_entries(
        self,
        entries: list[str | DiscoveryEntry],
        *,
        search_url: str,
    ) -> list[DiscoveryEntry]:
        normalized: list[DiscoveryEntry] = []
        for index, entry in enumerate(entries):
            if isinstance(entry, str):
                normalized.append(
                    {
                        "url": entry,
                        "listing_position": index,
                        "search_url": search_url,
                        "listing_data": {},
                    }
                )
                continue
            url = entry.get("url")
            if not url:
                logger.warning(
                    "%s Skipping discovery entry without url for %s",
                    LogTag.WARN,
                    self.source_name,
                )
                continue
            normalized.append(
                {
                    "url": url,
                    "listing_position": entry.get("listing_position", index),
                    "search_url": entry.get("search_url", search_url),
                    "listing_data": entry.get("listing_data", {}),
                    "listing_link": entry.get("listing_link"),
                    "listing_snippet": entry.get("listing_snippet"),
                }
            )
        return normalized

    def _parse_extracted_content(
        self, result: Any
    ) -> dict[str, Any] | list[Any] | None:
        if not result.extracted_content:
            return None
        try:
            return json.loads(result.extracted_content)
        except Exception:
            return {"raw": result.extracted_content}

    def _listing_artifacts(
        self,
        *,
        discovery_entry: DiscoveryEntry | None,
        listing_result: Any | None,
    ) -> dict[str, Any] | None:
        if not discovery_entry and not listing_result:
            return None
        payload: dict[str, Any] = {
            "search_url": discovery_entry.get("search_url")
            if discovery_entry
            else None,
            "listing_position": (
                discovery_entry.get("listing_position") if discovery_entry else None
            ),
            "listing_data": discovery_entry.get("listing_data", {})
            if discovery_entry
            else {},
            "listing_link": discovery_entry.get("listing_link")
            if discovery_entry
            else None,
            "listing_snippet": (
                discovery_entry.get("listing_snippet") if discovery_entry else None
            ),
        }
        if listing_result is not None:
            payload["listing_page_url"] = listing_result.url
        return payload

    async def _extract_payload(
        self,
        result: Any,
        *,
        discovery_entry: DiscoveryEntry | None = None,
        scraped_at: datetime,
    ) -> tuple[dict | None, dict | None, str, str | None]:
        valid_data = None
        merged_payload = None
        extraction_method = "none"
        extraction_error = None
        css_error = None

        if result.extracted_content:
            raw_payload, parse_error = self._parse_payload(result.extracted_content)
            merged_payload = self._merge_listing_into_payload(
                payload=raw_payload,
                listing_case=self._listing_case_payload(
                    discovery_entry=discovery_entry,
                    scraped_at=scraped_at,
                ),
            )
            valid_data, css_error = self._validate_payload(merged_payload)
            if parse_error and not css_error:
                css_error = parse_error
            if valid_data:
                extraction_method = "css"
                logger.info("%s %s extracted and validated.", LogTag.FAST, result.url)

        if not valid_data:
            llm_payload, llm_error = await self._llm_rescue(self._markdown_text(result))
            merged_payload = self._merge_listing_into_payload(
                payload=llm_payload,
                listing_case=self._listing_case_payload(
                    discovery_entry=discovery_entry,
                    scraped_at=scraped_at,
                ),
            )
            valid_data, validation_error = self._validate_payload(merged_payload)
            if valid_data:
                extraction_method = "llm"
                logger.info("%s %s rescued by LLM.", LogTag.OK, result.url)
            else:
                extraction_error = (
                    f"CSS Error: {css_error} | LLM Error: {llm_error} | "
                    f"Validation Error: {validation_error}"
                )
                logger.error(
                    "%s %s structured extraction failed: %s",
                    LogTag.FAIL,
                    result.url,
                    validation_error or llm_error,
                )

        return valid_data, merged_payload, extraction_method, extraction_error

    def _meta_log(
        self,
        *,
        result: Any,
        job_id: str,
        scraped_at: datetime,
        valid_data: dict | None,
        extraction_method: str,
        extraction_error: str | None,
    ) -> dict[str, Any]:
        return {
            "timestamp": scraped_at.isoformat(),
            "job_id": job_id,
            "url": result.url,
            "success": result.success and valid_data is not None,
            "extraction_method": extraction_method,
            "error": extraction_error or result.error_message,
            "crawl_stats": result.crawl_stats or {},
            "response_status": result.status_code,
        }

    def _persist_result(
        self,
        *,
        job_id: str,
        result: Any,
        valid_data: dict | None,
        merged_payload: dict | None,
        extraction_method: str,
        extraction_error: str | None,
        scraped_at: datetime,
        discovery_entry: DiscoveryEntry | None = None,
        listing_result: Any | None = None,
        node_name: str = "ingest",
    ) -> str:
        listing_case = self._listing_case_payload(
            discovery_entry=discovery_entry,
            scraped_at=scraped_at,
        )
        artifact_stage = "proposed" if valid_data else "failed"
        payload = dict(valid_data or merged_payload or {})
        if valid_data and merged_payload and merged_payload.get("listing_case"):
            payload["listing_case"] = merged_payload["listing_case"]
        content = self._markdown_text(result)
        if payload and not payload.get("original_language"):
            payload["original_language"] = detect_language(content)
        refs = self.data_manager.ingest_raw_job(
            source=self.source_name,
            job_id=job_id,
            payload=payload,
            content=content,
            metadata=self._meta_log(
                result=result,
                job_id=job_id,
                scraped_at=scraped_at,
                valid_data=valid_data,
                extraction_method=extraction_method,
                extraction_error=extraction_error,
            ),
            raw_html=getattr(result, "html", "") or "",
            cleaned_html=result.cleaned_html or "",
            node_name=node_name,
            stage=artifact_stage,
        )
        raw_extracted = self._parse_extracted_content(result)
        if raw_extracted is not None:
            refs["raw_extracted"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="raw_extracted.json",
                data={"data": raw_extracted},
            )
        listing_payload = self._listing_artifacts(
            discovery_entry=discovery_entry,
            listing_result=listing_result,
        )
        if listing_payload is not None:
            refs["listing"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="listing.json",
                data=listing_payload,
            )
        if listing_case is not None:
            refs["listing_case"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="listing_case.json",
                data=listing_case,
            )
            listing_case_markdown = (
                discovery_entry.get("listing_snippet") if discovery_entry else None
            )
            if listing_case_markdown:
                refs["listing_case_content"] = self.data_manager.write_text_artifact(
                    source=self.source_name,
                    job_id=job_id,
                    node_name=node_name,
                    stage=artifact_stage,
                    filename="listing_case.md",
                    content=listing_case_markdown,
                )
            listing_case_html = (
                discovery_entry.get("listing_case_html") if discovery_entry else None
            )
            if listing_case_html:
                refs["listing_case_html"] = self.data_manager.write_text_artifact(
                    source=self.source_name,
                    job_id=job_id,
                    node_name=node_name,
                    stage=artifact_stage,
                    filename="listing_case.html",
                    content=listing_case_html,
                )
            listing_case_cleaned_html = (
                discovery_entry.get("listing_case_cleaned_html")
                if discovery_entry
                else None
            )
            if listing_case_cleaned_html:
                refs["listing_case_cleaned_html"] = (
                    self.data_manager.write_text_artifact(
                        source=self.source_name,
                        job_id=job_id,
                        node_name=node_name,
                        stage=artifact_stage,
                        filename="listing_case.cleaned.html",
                        content=listing_case_cleaned_html,
                    )
                )
        if listing_result is not None:
            listing_markdown = self._markdown_text(listing_result)
            if listing_markdown:
                refs["listing_content"] = self.data_manager.write_text_artifact(
                    source=self.source_name,
                    job_id=job_id,
                    node_name=node_name,
                    stage=artifact_stage,
                    filename="listing_content.md",
                    content=listing_markdown,
                )
            if getattr(listing_result, "html", None):
                refs["listing_html"] = self.data_manager.write_text_artifact(
                    source=self.source_name,
                    job_id=job_id,
                    node_name=node_name,
                    stage=artifact_stage,
                    filename="listing_page.html",
                    content=listing_result.html,
                )
            if listing_result.cleaned_html:
                refs["listing_cleaned_html"] = self.data_manager.write_text_artifact(
                    source=self.source_name,
                    job_id=job_id,
                    node_name=node_name,
                    stage=artifact_stage,
                    filename="listing_page.cleaned.html",
                    content=listing_result.cleaned_html,
                )
        return job_id

    async def _process_results(
        self,
        *,
        results: list[Any],
        discovery_entries: dict[str, DiscoveryEntry] | None = None,
        listing_result: Any | None = None,
        node_name: str = "ingest",
    ) -> list[str]:
        ingested_job_ids: list[str] = []
        for result in results:
            job_id = self.extract_job_id(result.url)
            if not result.success:
                logger.error("%s %s: %s", LogTag.FAIL, job_id, result.error_message)
                continue
            scraped_at = _now_utc()
            (
                valid_data,
                merged_payload,
                extraction_method,
                extraction_error,
            ) = await self._extract_payload(
                result,
                discovery_entry=(discovery_entries or {}).get(result.url),
                scraped_at=scraped_at,
            )
            self._persist_result(
                job_id=job_id,
                result=result,
                valid_data=valid_data,
                merged_payload=merged_payload,
                extraction_method=extraction_method,
                extraction_error=extraction_error,
                scraped_at=scraped_at,
                discovery_entry=(discovery_entries or {}).get(result.url),
                listing_result=listing_result,
                node_name=node_name,
            )
            if valid_data:
                ingested_job_ids.append(job_id)
        return ingested_job_ids

    async def run(
        self,
        already_scraped: list[str],
        save_html: bool = False,
        **kwargs,
    ) -> list[str]:
        """Discover jobs from a source and ingest them canonically."""
        search_url = self.get_search_url(**kwargs)
        drop_repeated = kwargs.get("drop_repeated", True)

        async with AsyncWebCrawler(config=self.get_browser_config()) as crawler:
            logger.info("%s Searching for jobs at: %s", LogTag.FAST, search_url)
            listing_result = await crawler.arun(
                url=search_url, config=self.get_base_crawl_config()
            )
            if not listing_result.success:
                logger.error(
                    "%s Search failed: %s", LogTag.FAIL, listing_result.error_message
                )
                return []

            discovery_entries = self._normalize_discovery_entries(
                self.extract_links(listing_result),
                search_url=search_url,
            )
            links_to_crawl: list[DiscoveryEntry] = []
            for entry in discovery_entries:
                url = entry["url"]
                job_id = self.extract_job_id(url)
                if drop_repeated and job_id in already_scraped:
                    continue
                links_to_crawl.append(entry)

            if not links_to_crawl:
                logger.info("%s No new job postings.", LogTag.SKIP)
                return []

            limit = kwargs.get("limit")
            if limit:
                links_to_crawl = links_to_crawl[:limit]

            crawl_urls = [entry["url"] for entry in links_to_crawl]
            schema = await self.get_fast_schema(crawler, crawl_urls[0])
            run_config = self.get_base_crawl_config()
            if schema:
                run_config.extraction_strategy = JsonCssExtractionStrategy(schema)

            logger.info(
                "%s Processing %s jobs for %s",
                LogTag.FAST,
                len(links_to_crawl),
                self.source_name,
            )
            results = await crawler.arun_many(
                urls=crawl_urls,
                config=run_config,
                dispatcher=self.get_dispatcher(),
            )
            return await self._process_results(
                results=results,
                discovery_entries={entry["url"]: entry for entry in links_to_crawl},
                listing_result=listing_result,
            )

    async def fetch_job(self, url: str, *, save_html: bool = False) -> str:
        """Fetch and ingest a single explicit job URL."""
        async with AsyncWebCrawler(config=self.get_browser_config()) as crawler:
            schema = await self.get_fast_schema(crawler, url)
            run_config = self.get_base_crawl_config()
            if schema:
                run_config.extraction_strategy = JsonCssExtractionStrategy(schema)
            result = await crawler.arun(url=url, config=run_config)
            if not result.success:
                raise RuntimeError(
                    f"Failed to fetch job at {url}: {result.error_message}"
                )
            ingested_job_ids = await self._process_results(
                results=[result],
            )
        if not ingested_job_ids:
            raise RuntimeError(f"Job fetch produced no ingested artifact for {url}")
        return ingested_job_ids[0]
