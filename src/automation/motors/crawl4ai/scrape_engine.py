"""Shared scraper base for canonical job ingestion."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
    RateLimiter,
    SemaphoreDispatcher,
)
from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    LLMExtractionStrategy,
)
from dotenv import load_dotenv

try:
    from langdetect import DetectorFactory, detect_langs
    from langdetect.lang_detect_exception import LangDetectException

    DetectorFactory.seed = 0
except ImportError:  # pragma: no cover - exercised in environments without langdetect
    detect_langs = None
    LangDetectException = None

from src.automation.motors.crawl4ai.contracts import (
    DiscoverySourceContract,
    ScrapeDiscoveryEntry,
)
from src.core.data_manager import DataManager
from src.automation.ariadne.job_normalization import (
    clean_location_text,
    detect_employment_type_from_text,
    extract_job_title_from_markdown,
    hero_markdown_value,
    listing_case_metadata_value,
    merge_rescue_payloads,
    mine_bullets_from_markdown,
    normalize_job_payload,
)
from src.automation.ariadne.models import (
    ApplicationRoutingInterpretation,
    JobPosting,
)
from src.shared.log_tags import LogTag

load_dotenv()

logger = logging.getLogger(__name__)


DiscoveryEntryInput = str | dict[str, Any] | ScrapeDiscoveryEntry

_LANGUAGE_TOKEN_RE = re.compile(r"[a-zA-Zäöüß]+")
_GERMAN_LANGUAGE_HINTS = {
    "als",
    "aufgaben",
    "ausbildung",
    "berlin",
    "bewerbung",
    "deine",
    "deutsch",
    "du",
    "erfahrung",
    "fähigkeiten",
    "für",
    "gesucht",
    "heute",
    "ingenieur",
    "kenntnisse",
    "mit",
    "standort",
    "stelle",
    "team",
    "und",
    "wir",
}
_ENGLISH_LANGUAGE_HINTS = {
    "and",
    "build",
    "data",
    "engineer",
    "english",
    "experience",
    "for",
    "hiring",
    "location",
    "pipelines",
    "python",
    "remote",
    "requirements",
    "responsibilities",
    "role",
    "sql",
    "team",
    "the",
    "we",
    "with",
    "your",
}
_GERMAN_LANGUAGE_FRAGMENTS = ("ingenieur", "entwickler", "kenntnis", "bewerb", "aufgab")
_ENGLISH_LANGUAGE_FRAGMENTS = ("engineer", "developer", "scientist", "manager")
_SCHEMA_SELECTOR_BLOCKLIST = re.compile(
    r"related|similar|recommend|teaser|carousel|footer|sticky|other-jobs|jobs-nearby",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s)\]>\"']+", re.IGNORECASE)
_APPLY_LINK_RE = re.compile(
    r"(?:apply|application|bewerb|bewerben|bewerbung|jetzt bewerben|send your application)"
    r".{0,120}?(https?://[^\s)\]>\"']+)",
    re.IGNORECASE | re.DOTALL,
)
_JOB_PATH_HINT_RE = re.compile(
    r"/(?:jobs?|job-board|jobboard|jobpostings?|careers?|career|positions?|openings?|vacancies?|vacancy|requisitions?)(?:/|$)",
    re.IGNORECASE,
)
_JOB_QUERY_HINT_RE = re.compile(
    r"(?:^|[?&])(gh_jid|lever-source|lever-via|job|jobid|job_id|jobreq|reqid|posting|posting_id|requisition)="
)
_JOB_TEXT_HINT_RE = re.compile(
    r"job|opening|position|role|career|vacancy|bewerb|karriere|stellen|stelle",
    re.IGNORECASE,
)
_APPLY_ONLY_RE = re.compile(
    r"/(?:apply|application|submit|candidate|signup|register)(?:/|$)",
    re.IGNORECASE,
)
_ASSET_PATH_RE = re.compile(
    r"\.(?:css|js|json|xml|png|jpe?g|gif|svg|webp|pdf|zip|ico)(?:$|[?#])",
    re.IGNORECASE,
)
_ATS_HOST_HINT_RE = re.compile(
    r"greenhouse|lever|workday|smartrecruiters|ashby|personio|join|teamtailor|recruitee|jobylon|workable|icims|successfactors|myworkdayjobs",
    re.IGNORECASE,
)


def _language_tokens(text: str) -> list[str]:
    return [token.lower() for token in _LANGUAGE_TOKEN_RE.findall(text)]


def _count_hint_matches(
    tokens: Iterable[str], hints: set[str], fragments: tuple[str, ...]
) -> int:
    matches = 0
    for token in tokens:
        if token in hints:
            matches += 1
            continue
        if any(fragment in token for fragment in fragments):
            matches += 1
    return matches


def _heuristic_language_scores(text: str) -> dict[str, float]:
    tokens = _language_tokens(text)
    lowered = text.lower()
    german_matches = _count_hint_matches(
        tokens,
        _GERMAN_LANGUAGE_HINTS,
        _GERMAN_LANGUAGE_FRAGMENTS,
    )
    english_matches = _count_hint_matches(
        tokens,
        _ENGLISH_LANGUAGE_HINTS,
        _ENGLISH_LANGUAGE_FRAGMENTS,
    )
    return {
        "de": german_matches * 2.0 + sum(ch in text for ch in "äöüß") * 3.0,
        "en": english_matches * 2.0 + lowered.count(" the ") + lowered.count(" and "),
    }


def _langdetect_scores(text: str) -> dict[str, float]:
    if detect_langs is None:
        return {}
    try:
        candidates = detect_langs(text)
    except LangDetectException:
        return {}
    return {
        candidate.lang: candidate.prob
        for candidate in candidates
        if candidate.lang in {"de", "en"}
    }


def _language_sample(markdown_text: str) -> str:
    sample = re.sub(r"\s+", " ", markdown_text).strip()
    return sample[:1000]


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


def detect_language(markdown_text: str) -> str:
    """Detect the primary posting language, preferring langdetect with lexical fallback."""
    sample = _language_sample(markdown_text)
    if not sample:
        return "en"

    tokens = _language_tokens(sample)
    heuristic_scores = _heuristic_language_scores(sample)
    detector_scores = _langdetect_scores(sample)
    detector_weight = 3.0 if len(tokens) >= 6 and len(sample) >= 48 else 0.75
    combined_scores = {
        "de": heuristic_scores["de"] + detector_scores.get("de", 0.0) * detector_weight,
        "en": heuristic_scores["en"] + detector_scores.get("en", 0.0) * detector_weight,
    }
    if combined_scores["de"] == combined_scores["en"]:
        return (
            "de"
            if detector_scores.get("de", 0.0) > detector_scores.get("en", 0.0)
            else "en"
        )
    return "de" if combined_scores["de"] > combined_scores["en"] else "en"


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split()).strip()
    return cleaned or None


def _normalize_application_email(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    if cleaned.lower().startswith("mailto:"):
        cleaned = cleaned.split(":", 1)[1]
    cleaned = cleaned.split("?", 1)[0].strip(" <>.,;)")
    match = _EMAIL_RE.search(cleaned)
    return match.group(0).lower() if match else None


def _normalize_application_url(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned or cleaned.lower().startswith("mailto:"):
        return None
    match = _URL_RE.search(cleaned)
    if not match:
        return None
    return match.group(0).rstrip(".,;")


def _normalize_application_method(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if any(token in lowered for token in ("email", "e-mail", "mail", "bewerbung an")):
        return "email"
    if any(
        token in lowered
        for token in (
            "direct",
            "external",
            "portal",
            "website",
            "online",
            "link",
            "url",
        )
    ):
        return "direct_url"
    if any(
        token in lowered for token in ("onsite", "current page", "form", "easy apply")
    ):
        return "onsite"
    return lowered.replace(" ", "_")


def _first_email_match(*values: Any) -> str | None:
    for value in values:
        email = _normalize_application_email(value)
        if email:
            return email
    return None


def _normalized_hostname(url: str | None) -> str | None:
    cleaned = _clean_text(url)
    if not cleaned:
        return None
    hostname = urlparse(cleaned).hostname
    if not hostname:
        return None
    return hostname.lower().removeprefix("www.")


def _same_domain_scope(candidate_url: str, scope_host: str) -> bool:
    candidate_host = _normalized_hostname(candidate_url)
    if not candidate_host:
        return False
    return candidate_host == scope_host or candidate_host.endswith(f".{scope_host}")


def _company_source_name(company_domain: str) -> str:
    return f"company-{re.sub(r'[^a-z0-9._-]+', '-', company_domain.lower()).strip('-')}"


def _generic_job_id(url: str) -> str:
    parsed = urlparse(url)
    segments = [segment for segment in parsed.path.split("/") if segment]
    query_hint = parsed.query.replace("=", "-").replace("&", "-")
    raw_value = segments[-1] if segments else query_hint or parsed.netloc or "job"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", raw_value).strip("-").lower()
    if not slug:
        slug = "job"
    return slug[:80]


def _job_url_hints(url: str, *, text: str | None = None) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if _ASSET_PATH_RE.search(parsed.path):
        return False
    joined_text = " ".join(filter(None, [parsed.path, parsed.query, text or ""]))
    if _APPLY_ONLY_RE.search(parsed.path) and not _JOB_PATH_HINT_RE.search(parsed.path):
        return False
    if _JOB_PATH_HINT_RE.search(parsed.path):
        return True
    if _JOB_QUERY_HINT_RE.search(f"?{parsed.query}"):
        return True
    if _ATS_HOST_HINT_RE.search(parsed.netloc) and re.search(r"\d", joined_text):
        return True
    return bool(_JOB_TEXT_HINT_RE.search(joined_text))


def _cross_portal_seed_contract(
    *,
    company_domain: str,
    seed_url: str,
    upstream_source: str,
    upstream_job_id: str,
) -> DiscoverySourceContract:
    return DiscoverySourceContract(
        kind="company_domain",
        source_name=_company_source_name(company_domain),
        company_domain=company_domain,
        seed_url=seed_url,
        upstream_source=upstream_source,
        upstream_job_id=upstream_job_id,
    )


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
    def extract_links(self, crawl_result: Any) -> list[DiscoveryEntryInput]:
        """Return discovery entries from a listing result.

        Implementations should return typed discovery entries that preserve the
        listing-side metadata needed to build job-scoped artifacts.
        """

    @abstractmethod
    def get_llm_instructions(self) -> str:
        """Return portal-specific extraction hints."""

    def discovery_source_contract(self) -> DiscoverySourceContract:
        """Return the persistence contract for this adapter's discovery namespace."""
        return DiscoverySourceContract(kind="portal", source_name=self.source_name)

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
            Browser settings using Crawl4AI's local Chromium.
            BrowserOS injection is not used for scrape runs because real portal
            listing pages have proven more reliable with Crawl4AI's own browser
            than with the BrowserOS CDP-attached browser.
        """
        return BrowserConfig(
            browser_type="chromium",
            headless=True,
            text_mode=True,
        )

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

    @property
    def schema_generation_sample_size(self) -> int:
        """Return how many representative detail pages to use for schema learning."""
        return 3

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
            "The schema will be validated against multiple representative detail pages and rejected if it targets teaser or related-job modules.",
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

    class _TransientNetworkError(Exception):
        """Raised when a crawl fails with a transient network condition."""

        pass

    _TRANSIENT_ERROR_PATTERNS = (
        "net::ERR_NETWORK_CHANGED",
        "net::ERR_INTERNET_DISCONNECTED",
        "net::ERR_CONNECTION_RESET",
        "net::ERR_CONNECTION_TIMED_OUT",
        "net::ERR_NAME_NOT_RESOLVED",
    )

    async def _retry_crawl(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        config: Any,
        *,
        max_retries: int = 3,
    ) -> Any:
        """Retry a crawl up to max_retries on transient network errors.

        Each retry waits 2^(attempt) seconds (exponential backoff).
        Logs each attempt with LogTag.RETRY.
        """
        last_error: str | None = None
        for attempt in range(max_retries + 1):
            result = await crawler.arun(url=url, config=config)
            if result.success:
                return result
            error_msg = result.error_message or ""
            is_transient = any(
                pat in error_msg for pat in self._TRANSIENT_ERROR_PATTERNS
            )
            if not is_transient or attempt == max_retries:
                return result
            wait_seconds = 2**attempt
            logger.info(
                "%s Transient network error for %s (attempt %s/%s), retrying in %ss: %s",
                LogTag.RETRY,
                url,
                attempt + 1,
                max_retries + 1,
                wait_seconds,
                error_msg,
            )
            await crawler.sleep(wait_seconds)
        return None

    def _schema_sample_urls(
        self,
        *,
        sample_url: str,
        candidate_urls: Iterable[str] | None = None,
    ) -> list[str]:
        ordered_urls: list[str] = []
        for url in [sample_url, *(candidate_urls or [])]:
            if not url or url in ordered_urls:
                continue
            ordered_urls.append(url)
            if len(ordered_urls) >= self.schema_generation_sample_size:
                break
        return ordered_urls

    async def _load_schema_samples(
        self,
        crawler: AsyncWebCrawler,
        sample_urls: list[str],
    ) -> list[tuple[str, str]]:
        samples: list[tuple[str, str]] = []
        for url in sample_urls:
            result = await self._retry_crawl(crawler, url, self.get_base_crawl_config())
            if not result or not result.success or not result.cleaned_html:
                logger.warning(
                    "%s Skipping schema sample %s: %s",
                    LogTag.WARN,
                    url,
                    (result.error_message if result else "no result")
                    or "missing cleaned HTML",
                )
                continue
            samples.append((url, result.cleaned_html[:50000]))
        return samples

    def _iter_schema_selectors(self, schema: dict[str, Any]) -> Iterable[str]:
        base_selector = schema.get("baseSelector")
        if isinstance(base_selector, str) and base_selector.strip():
            yield base_selector

        stack = list(schema.get("fields") or [])
        while stack:
            field = stack.pop()
            selector = field.get("selector")
            if isinstance(selector, str) and selector.strip():
                yield selector
            stack.extend(field.get("fields") or [])

    def _schema_selector_violations(self, schema: dict[str, Any]) -> list[str]:
        violations: list[str] = []
        for selector in self._iter_schema_selectors(schema):
            if _SCHEMA_SELECTOR_BLOCKLIST.search(selector):
                violations.append(selector)
        return violations

    def _select_nodes(self, roots: list[Any], selector: str | None) -> list[Any]:
        if not selector or selector in {".", ":scope"}:
            return roots
        matches: list[Any] = []
        for root in roots:
            try:
                matches.extend(root.select(selector))
            except Exception:
                return []
        return matches

    def _field_matches_sample(self, field: dict[str, Any], roots: list[Any]) -> bool:
        matches = self._select_nodes(roots, field.get("selector"))
        if not matches:
            return False
        nested_fields = field.get("fields") or []
        if not nested_fields:
            return True
        return any(
            self._field_matches_sample(nested, matches) for nested in nested_fields
        )

    def _schema_sample_coverage(self, schema: dict[str, Any], html: str) -> float:
        fields = schema.get("fields") or []
        if not fields:
            return 0.0
        soup = BeautifulSoup(html, "html.parser")
        roots = self._select_nodes([soup], schema.get("baseSelector") or "body")
        if not roots:
            return 0.0
        matched_fields = sum(
            1 for field in fields if self._field_matches_sample(field, roots)
        )
        return matched_fields / len(fields)

    def _score_generated_schema(
        self,
        schema: dict[str, Any],
        sample_htmls: list[str],
    ) -> float | None:
        violations = self._schema_selector_violations(schema)
        if violations:
            logger.warning(
                "%s Rejecting schema with blocked selectors: %s",
                LogTag.WARN,
                ", ".join(violations),
            )
            return None

        coverages = [
            self._schema_sample_coverage(schema, html) for html in sample_htmls
        ]
        if not coverages or any(coverage <= 0.0 for coverage in coverages):
            return None
        return sum(coverages) / len(coverages)

    async def get_fast_schema(
        self,
        crawler: AsyncWebCrawler,
        sample_url: str,
        *,
        candidate_urls: Iterable[str] | None = None,
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
        sample_urls = self._schema_sample_urls(
            sample_url=sample_url,
            candidate_urls=candidate_urls,
        )
        samples = await self._load_schema_samples(crawler, sample_urls)
        if not samples:
            logger.error("%s Could not download sample page.", LogTag.FAIL)
            return None

        sample_htmls = [html for _, html in samples]
        best_schema: dict[str, Any] | None = None
        best_score = -1.0
        try:
            for _, html in samples:
                schema = JsonCssExtractionStrategy.generate_schema(
                    html=html,
                    schema_type="CSS",
                    target_json_example=json.dumps(
                        self._css_schema_target_example(), indent=2
                    ),
                    query=self._schema_generation_query(),
                    llm_config=self.get_llm_config(),
                )
                score = self._score_generated_schema(schema, sample_htmls)
                if score is None or score <= best_score:
                    continue
                best_schema = schema
                best_score = score
        except Exception as exc:
            logger.error("%s Error generating schema: %s", LogTag.FAIL, exc)
            return None

        if best_schema is None:
            logger.error(
                "%s No representative schema passed validation for %s.",
                LogTag.FAIL,
                self.source_name,
            )
            return None

        self.schema_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.schema_cache_path.write_text(
            json.dumps(best_schema, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info(
            "%s CSS schema generated from %s representative samples and cached.",
            LogTag.OK,
            len(samples),
        )
        return best_schema

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

    def _llm_rescue_instruction(self) -> str:
        """Return the Crawl4AI-native instruction used for fallback extraction."""
        instructions = [self.get_llm_instructions().strip()]
        instructions.append(
            "Extract the job posting into the provided schema."
            " Return only values supported by the page content."
        )
        return "\n\n".join(part for part in instructions if part)

    def get_extraction_fallback_order(self) -> tuple[str, ...]:
        """Return the configured rescue order after CSS extraction fails.

        The order is configured via ``AUTOMATION_EXTRACTION_FALLBACKS`` as a
        comma-separated list. Supported values are ``browseros`` and ``llm``.
        The default is ``browseros`` so live scraping does not depend on a
        Gemini key unless explicitly enabled.
        """
        raw = os.environ.get("AUTOMATION_EXTRACTION_FALLBACKS", "browseros")
        allowed = {"browseros", "llm"}
        ordered: list[str] = []
        for item in raw.split(","):
            name = item.strip().lower()
            if not name or name not in allowed or name in ordered:
                continue
            ordered.append(name)
        return tuple(ordered)

    def _browseros_payload_text(self, value: Any) -> str:
        """Flatten BrowserOS MCP payloads into one text blob."""
        chunks: list[str] = []

        def _walk(node: Any) -> None:
            if isinstance(node, str):
                if node.strip():
                    chunks.append(node)
                return
            if isinstance(node, dict):
                for child in node.values():
                    _walk(child)
                return
            if isinstance(node, list):
                for child in node:
                    _walk(child)

        _walk(value)
        return "\n".join(chunks)

    def _extract_job_title_from_markdown(self, markdown_text: str) -> str | None:
        """Return the first plausible title heading from page markdown."""
        return extract_job_title_from_markdown(markdown_text)

    def _detect_employment_type_from_text(self, markdown_text: str) -> str | None:
        """Infer employment type from page text when the teaser did not provide it."""
        return detect_employment_type_from_text(markdown_text)

    def _clean_location_text(self, value: Any) -> str | None:
        """Normalize noisy location strings from hero and teaser content."""
        return clean_location_text(value)

    def _hero_markdown_value(self, markdown_text: str, *, field: str) -> str | None:
        """Recover scalar values from hero-style markdown content."""
        return hero_markdown_value(markdown_text, field=field)

    def _merge_rescue_payloads(
        self,
        *,
        base_payload: dict | None,
        rescue_payload: dict | None,
    ) -> dict | None:
        """Merge rescue output onto the best existing CSS payload."""
        return merge_rescue_payloads(
            base_payload=base_payload,
            rescue_payload=rescue_payload,
        )

    def _listing_case_metadata_value(
        self,
        listing_case: dict[str, Any],
        *,
        field: str,
    ) -> str | None:
        """Recover company/location from listing metadata when teaser fields are noisy."""
        return listing_case_metadata_value(listing_case, field=field)

    def _build_browseros_payload_from_text(self, markdown_text: str) -> dict[str, Any]:
        """Build a minimal structured payload from BrowserOS MCP page content."""
        payload: dict[str, Any] = {}
        title = self._extract_job_title_from_markdown(markdown_text)
        if title:
            payload["job_title"] = title
        company_name = self._hero_markdown_value(markdown_text, field="company_name")
        if company_name:
            payload["company_name"] = company_name
        location = self._hero_markdown_value(markdown_text, field="location")
        if location:
            payload["location"] = location
        bullets = self._mine_bullets_from_markdown(markdown_text)
        if bullets.get("responsibilities"):
            payload["responsibilities"] = bullets["responsibilities"]
        if bullets.get("requirements"):
            payload["requirements"] = bullets["requirements"]
        employment_type = self._detect_employment_type_from_text(markdown_text)
        if employment_type:
            payload["employment_type"] = employment_type
        return payload

    def _validate_payload(self, payload: dict | None) -> tuple[dict | None, str | None]:
        """Validate a merged payload against the job posting contract."""
        if not payload:
            return None, "No payload to validate."
        try:
            return JobPosting(**payload).model_dump(), None
        except Exception as exc:
            return None, str(exc)

    def _init_normalization_diagnostics(self) -> dict[str, Any]:
        """Create the default normalization diagnostics payload."""
        return {
            "field_sources": {},
            "operations": [],
        }

    def _record_field_source(
        self,
        diagnostics: dict[str, Any],
        *,
        field: str,
        source: str,
    ) -> None:
        """Record which stage produced a cleaned field."""
        diagnostics.setdefault("field_sources", {})[field] = source

    def _record_operation(self, diagnostics: dict[str, Any], operation: str) -> None:
        """Record a normalization operation once."""
        operations = diagnostics.setdefault("operations", [])
        if operation not in operations:
            operations.append(operation)

    def _normalize_payload_with_diagnostics(
        self,
        payload: dict | None,
        *,
        result: Any | None = None,
        listing_case: dict | None = None,
        rescue_source: str | None = None,
        existing_diagnostics: dict[str, Any] | None = None,
    ) -> tuple[dict | None, dict[str, Any]]:
        """Normalize a payload and capture cleanup provenance."""
        result_markdown = self._markdown_text(result) if result is not None else ""
        normalized = normalize_job_payload(
            payload,
            markdown_text=result_markdown,
            listing_case=listing_case,
            rescue_source=rescue_source,
            existing_diagnostics=existing_diagnostics,
        )
        return normalized.payload or None, normalized.diagnostics

    def _normalize_payload(
        self,
        payload: dict | None,
        *,
        result: Any | None = None,
        listing_case: dict | None = None,
    ) -> dict | None:
        """Normalize a payload after merge, before validation."""
        normalized, _ = self._normalize_payload_with_diagnostics(
            payload,
            result=result,
            listing_case=listing_case,
        )
        return normalized

    def _finalize_extracted_payload(
        self,
        *,
        payload: dict,
        cleaned_payload: dict,
    ) -> dict:
        """Build the final validated payload from the cleaned stage."""
        finalized = dict(payload)
        if cleaned_payload.get("listing_case"):
            finalized["listing_case"] = cleaned_payload["listing_case"]
        return finalized

    def _mine_bullets_from_markdown(self, markdown: str) -> dict[str, list[str]]:
        """Extract responsibilities / requirements bullet lists from German markdown sections.

        Known German heading patterns (case-insensitive):
          Responsibilities: "Das erwartet Dich", "Deine Aufgaben", "Aufgaben", "Ihre Aufgaben"
          Requirements:     "Das bringst Du mit", "Dein Profil", "Anforderungen", "Ihre Qualifikationen"
        """
        return mine_bullets_from_markdown(markdown)

    async def _llm_rescue(
        self, crawler: AsyncWebCrawler | None, url: str, markdown_content: str
    ) -> tuple[dict | None, str | None]:
        """Use Crawl4AI's LLM extraction strategy as the fallback extractor."""
        if not self._has_llm_key() or not markdown_content:
            return None, "No LLM API key or empty markdown content."
        if crawler is None:
            return None, "LLM rescue requires an active crawler session."

        logger.info("%s LLM rescue for %s", LogTag.FALLBACK, self.source_name)
        try:
            llm_cfg = self.get_llm_config()
            run_config = self.get_base_crawl_config()
            run_config.extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_cfg,
                instruction=self._llm_rescue_instruction(),
                schema=JobPosting.model_json_schema(),
                input_format="markdown",
                force_json_response=True,
                extra_args={"temperature": llm_cfg.temperature or 0.1},
            )
            rescue_result = await crawler.arun(url=url, config=run_config)
            if not rescue_result.success:
                return None, rescue_result.error_message or "LLM rescue crawl failed."
            return self._parse_payload(rescue_result.extracted_content)
        except Exception as exc:
            logger.error("%s LLM rescue error: %s", LogTag.FAIL, exc)
            return None, f"LLM exception: {exc}"

    async def _browseros_rescue(
        self,
        url: str,
        markdown_content: str,
    ) -> tuple[dict | None, str | None]:
        """Use BrowserOS MCP page-content tools as a schema-free fallback."""
        try:
            from src.automation.motors.browseros.cli.client import BrowserOSClient
        except Exception as exc:
            return None, f"BrowserOS import failed: {exc}"

        logger.info("%s BrowserOS MCP rescue for %s", LogTag.FALLBACK, self.source_name)
        page_id: int | None = None
        try:
            client = BrowserOSClient()
            page_id = await asyncio.to_thread(client.new_hidden_page, url)
            await asyncio.to_thread(client.navigate, url, page_id)
            await asyncio.sleep(2.5)
            page_content = await asyncio.to_thread(client.get_page_content, page_id)
            extracted_markdown = self._browseros_payload_text(page_content).strip()
            if not extracted_markdown:
                dom_payload = await asyncio.to_thread(client.get_dom, page_id)
                extracted_markdown = self._browseros_payload_text(dom_payload).strip()
            if not extracted_markdown:
                extracted_markdown = markdown_content.strip()
            payload = self._build_browseros_payload_from_text(extracted_markdown)
            if not payload:
                return (
                    None,
                    "BrowserOS MCP rescue could not derive a payload from page content.",
                )
            return payload, None
        except Exception as exc:
            logger.error("%s BrowserOS rescue error: %s", LogTag.FAIL, exc)
            return None, f"BrowserOS exception: {exc}"
        finally:
            if page_id is not None:
                try:
                    await asyncio.to_thread(client.close_page, page_id)
                except Exception:
                    logger.warning(
                        "%s Failed to close BrowserOS rescue page %s",
                        LogTag.WARN,
                        page_id,
                    )

    def _routing_markdown_text(self, result: Any) -> str:
        return self._markdown_text(result)

    def _routing_heuristics(
        self,
        *,
        payload: dict,
        detail_url: str,
        markdown_text: str,
    ) -> dict[str, Any]:
        instructions = _clean_text(payload.get("application_instructions"))
        email = _first_email_match(
            payload.get("application_email"),
            payload.get("contact_info"),
            instructions,
            markdown_text,
        )
        explicit_url = _normalize_application_url(payload.get("application_url"))
        hinted_url = None
        apply_link_match = _APPLY_LINK_RE.search(markdown_text)
        if apply_link_match:
            hinted_url = _normalize_application_url(apply_link_match.group(1))
        direct_url = explicit_url or hinted_url
        method = _normalize_application_method(payload.get("application_method"))

        field_sources = {
            "application_method": "payload" if method else None,
            "application_url": None,
            "application_email": None,
            "application_instructions": "payload" if instructions else None,
        }
        signals: list[str] = []

        if email:
            field_sources["application_email"] = (
                "payload"
                if payload.get("application_email") or payload.get("contact_info")
                else "markdown"
            )
            signals.append("email")
        if direct_url:
            field_sources["application_url"] = "payload" if explicit_url else "markdown"
            signals.append("direct_url")

        if not method:
            if email:
                method = "email"
                field_sources["application_method"] = "derived_from_email"
            elif direct_url and direct_url != detail_url:
                method = "direct_url"
                field_sources["application_method"] = "derived_from_url"
            else:
                method = "onsite"
                field_sources["application_method"] = "detail_page_fallback"

        selected_url = direct_url
        if not selected_url:
            selected_url = detail_url
            field_sources["application_url"] = "detail_page_fallback"

        confidence = 0.25
        if payload.get("application_method"):
            confidence += 0.2
        if explicit_url:
            confidence += 0.25
        elif direct_url:
            confidence += 0.15
        elif selected_url == detail_url:
            confidence += 0.05
        if payload.get("application_email"):
            confidence += 0.2
        elif email:
            confidence += 0.1
        if instructions:
            confidence += 0.1
        if method == "email" and email:
            confidence += 0.15
        elif method in {"direct_url", "onsite"} and selected_url:
            confidence += 0.1
        confidence = min(confidence, 0.95)

        review_required = (
            confidence < 0.7
            or field_sources["application_url"] == "detail_page_fallback"
        )
        diagnostics = {
            "source": self.source_name,
            "used_llm": False,
            "review_required": review_required,
            "field_sources": field_sources,
            "signals": signals,
        }

        return {
            "application_method": method,
            "application_url": selected_url,
            "application_email": email,
            "application_instructions": instructions,
            "application_routing_confidence": round(confidence, 2),
            "application_routing_diagnostics": diagnostics,
        }

    async def _llm_routing_interpretation(
        self,
        crawler: AsyncWebCrawler | None,
        *,
        url: str,
        markdown_text: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if not self._has_llm_key() or not markdown_text:
            return None, "No LLM API key or empty markdown content."
        if crawler is None:
            return None, "Routing enrichment requires an active crawler session."

        logger.info("%s Routing enrichment for %s", LogTag.LLM, self.source_name)
        try:
            llm_cfg = self.get_llm_config()
            run_config = self.get_base_crawl_config()
            run_config.extraction_strategy = LLMExtractionStrategy(
                llm_config=llm_cfg,
                instruction=(
                    "Resolve how the candidate should apply. "
                    "Use application_method=email when the posting asks for email submission, "
                    "direct_url when a separate apply link exists, and onsite when the current page owns the form or apply button. "
                    f"If no separate apply link exists, keep application_url as {url}."
                ),
                schema=ApplicationRoutingInterpretation.model_json_schema(),
                input_format="markdown",
                force_json_response=True,
                extra_args={"temperature": 0.0},
            )
            rescue_result = await crawler.arun(url=url, config=run_config)
            if not rescue_result.success:
                return (
                    None,
                    rescue_result.error_message or "Routing enrichment crawl failed.",
                )
            payload, parse_error = self._parse_payload(rescue_result.extracted_content)
            if not payload:
                return None, parse_error or "Routing enrichment returned empty payload."
            routing = ApplicationRoutingInterpretation(**payload)
            return routing.model_dump(mode="python"), None
        except Exception as exc:
            logger.error("%s Routing enrichment error: %s", LogTag.FAIL, exc)
            return None, f"LLM exception: {exc}"

    async def _enrich_application_routing(
        self,
        *,
        payload: dict | None,
        result: Any,
        crawler: AsyncWebCrawler | None,
    ) -> dict | None:
        if payload is None:
            return None

        enriched = dict(payload)
        heuristic = self._routing_heuristics(
            payload=enriched,
            detail_url=result.url,
            markdown_text=self._routing_markdown_text(result),
        )
        enriched.update(heuristic)

        diagnostics = dict(enriched.get("application_routing_diagnostics") or {})
        diagnostics.setdefault("field_sources", {})

        if heuristic["application_routing_confidence"] >= 0.7:
            enriched["application_routing_diagnostics"] = diagnostics
            return enriched

        llm_payload, llm_error = await self._llm_routing_interpretation(
            crawler,
            url=result.url,
            markdown_text=self._routing_markdown_text(result),
        )
        diagnostics["llm_error"] = llm_error
        diagnostics["used_llm"] = llm_payload is not None

        if llm_payload:
            llm_method = _normalize_application_method(
                llm_payload.get("application_method")
            )
            llm_url = _normalize_application_url(llm_payload.get("application_url"))
            llm_email = _normalize_application_email(
                llm_payload.get("application_email")
            )
            llm_instructions = _clean_text(llm_payload.get("application_instructions"))

            if llm_method:
                enriched["application_method"] = llm_method
                diagnostics["field_sources"]["application_method"] = "llm"
            if (
                llm_url
                and diagnostics["field_sources"].get("application_url")
                == "detail_page_fallback"
            ):
                enriched["application_url"] = llm_url
                diagnostics["field_sources"]["application_url"] = "llm"
            if llm_email and not enriched.get("application_email"):
                enriched["application_email"] = llm_email
                diagnostics["field_sources"]["application_email"] = "llm"
            if llm_instructions and not enriched.get("application_instructions"):
                enriched["application_instructions"] = llm_instructions
                diagnostics["field_sources"]["application_instructions"] = "llm"

            if llm_method == "email" and llm_email:
                enriched["application_routing_confidence"] = 0.85
            elif llm_method in {"direct_url", "onsite"} and enriched.get(
                "application_url"
            ):
                enriched["application_routing_confidence"] = 0.8
            diagnostics["review_required"] = (
                enriched["application_routing_confidence"] < 0.8
            )
            diagnostics["llm_payload"] = llm_payload

        enriched["application_routing_diagnostics"] = diagnostics
        return enriched

    def _listing_case_payload(
        self,
        *,
        discovery_entry: ScrapeDiscoveryEntry | None,
        scraped_at: datetime,
    ) -> dict[str, Any] | None:
        if not discovery_entry:
            return None
        listing_data = discovery_entry.listing_data.model_dump(mode="python")
        listed_at_relative, listed_at_iso = normalize_relative_date(
            listing_data.get("posted_date"),
            scraped_at=scraped_at,
        )
        return {
            "job_id": discovery_entry.job_id,
            "url": discovery_entry.url,
            "search_url": discovery_entry.search_url,
            "listing_position": discovery_entry.listing_position,
            "scraped_at": scraped_at.isoformat(),
            "listed_at_relative": listed_at_relative,
            "listed_at_iso": listed_at_iso,
            "teaser_title": listing_data.get("job_title"),
            "teaser_company": listing_data.get("company_name"),
            "teaser_location": listing_data.get("location"),
            "teaser_salary": listing_data.get("salary"),
            "teaser_employment_type": listing_data.get("employment_type"),
            "teaser_text": discovery_entry.listing_snippet,
            "source_contract": (
                discovery_entry.source_contract.model_dump(mode="python")
                if discovery_entry.source_contract
                else None
            ),
            "source_metadata": discovery_entry.source_metadata,
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
        entries: list[DiscoveryEntryInput],
        *,
        search_url: str,
    ) -> list[ScrapeDiscoveryEntry]:
        normalized: list[ScrapeDiscoveryEntry] = []
        for index, entry in enumerate(entries):
            if isinstance(entry, str):
                normalized.append(
                    ScrapeDiscoveryEntry(
                        url=entry,
                        job_id=self.extract_job_id(entry),
                        listing_position=index,
                        search_url=search_url,
                        source_contract=self.discovery_source_contract(),
                    )
                )
                continue
            if isinstance(entry, ScrapeDiscoveryEntry):
                normalized.append(
                    entry.model_copy(
                        update={
                            "listing_position": (
                                entry.listing_position
                                if entry.listing_position is not None
                                else index
                            ),
                            "search_url": entry.search_url or search_url,
                            "source_contract": (
                                entry.source_contract
                                or self.discovery_source_contract()
                            ),
                        }
                    )
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
                ScrapeDiscoveryEntry(
                    url=url,
                    job_id=entry.get("job_id") or self.extract_job_id(url),
                    listing_position=entry.get("listing_position", index),
                    search_url=entry.get("search_url", search_url),
                    listing_data=entry.get("listing_data", {}),
                    listing_link=entry.get("listing_link"),
                    listing_snippet=entry.get("listing_snippet"),
                    source_contract=(
                        entry.get("source_contract")
                        or self.discovery_source_contract().model_dump(mode="python")
                    ),
                    source_metadata=entry.get("source_metadata", {}),
                )
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
        discovery_entry: ScrapeDiscoveryEntry | None,
        listing_result: Any | None,
    ) -> dict[str, Any] | None:
        if not discovery_entry and not listing_result:
            return None
        payload: dict[str, Any] = {
            "job_id": discovery_entry.job_id if discovery_entry else None,
            "search_url": discovery_entry.search_url if discovery_entry else None,
            "listing_position": discovery_entry.listing_position
            if discovery_entry
            else None,
            "listing_data": (
                discovery_entry.listing_data.model_dump(mode="python")
                if discovery_entry
                else {}
            ),
            "listing_link": discovery_entry.listing_link if discovery_entry else None,
            "listing_snippet": discovery_entry.listing_snippet
            if discovery_entry
            else None,
            "source_contract": (
                discovery_entry.source_contract.model_dump(mode="python")
                if discovery_entry and discovery_entry.source_contract
                else self.discovery_source_contract().model_dump(mode="python")
            ),
            "source_metadata": discovery_entry.source_metadata
            if discovery_entry
            else {},
        }
        if listing_result is not None:
            payload["listing_page_url"] = listing_result.url
        return payload

    async def _extract_payload(
        self,
        result: Any,
        *,
        crawler: AsyncWebCrawler | None = None,
        discovery_entry: ScrapeDiscoveryEntry | None = None,
        scraped_at: datetime,
    ) -> tuple[dict | None, dict | None, dict | None, str, str | None]:
        valid_data = None
        cleaned_payload = None
        css_payload = None
        normalization_diagnostics: dict[str, Any] | None = None
        extraction_method = "none"
        extraction_error = None
        css_error = None

        listing_case = self._listing_case_payload(
            discovery_entry=discovery_entry,
            scraped_at=scraped_at,
        )

        if result.extracted_content:
            raw_payload, parse_error = self._parse_payload(result.extracted_content)
            candidate_payload = self._merge_listing_into_payload(
                payload=raw_payload,
                listing_case=listing_case,
            )
            cleaned_payload, normalization_diagnostics = (
                self._normalize_payload_with_diagnostics(
                    candidate_payload,
                    result=result,
                    listing_case=listing_case,
                )
            )
            css_payload = dict(cleaned_payload or {})
            valid_data, css_error = self._validate_payload(cleaned_payload)
            if valid_data:
                routed_payload = await self._enrich_application_routing(
                    payload=cleaned_payload,
                    result=result,
                    crawler=crawler,
                )
                cleaned_payload, normalization_diagnostics = (
                    self._normalize_payload_with_diagnostics(
                        routed_payload,
                        result=result,
                        listing_case=listing_case,
                        existing_diagnostics=normalization_diagnostics,
                    )
                )
                valid_data, css_error = self._validate_payload(cleaned_payload)
            if parse_error and not css_error:
                css_error = parse_error
            if valid_data:
                valid_data = self._finalize_extracted_payload(
                    payload=valid_data,
                    cleaned_payload=cleaned_payload or {},
                )
                extraction_method = "css"
                logger.info("%s %s extracted and validated.", LogTag.FAST, result.url)

        if not valid_data:
            rescue_errors: list[str] = []
            validation_error = None
            for fallback_name in self.get_extraction_fallback_order():
                if fallback_name == "browseros":
                    rescue_payload, rescue_error = await self._browseros_rescue(
                        result.url,
                        self._markdown_text(result),
                    )
                elif fallback_name == "llm":
                    rescue_payload, rescue_error = await self._llm_rescue(
                        crawler,
                        result.url,
                        self._markdown_text(result),
                    )
                else:
                    continue

                candidate_payload = self._merge_listing_into_payload(
                    payload=self._merge_rescue_payloads(
                        base_payload=css_payload,
                        rescue_payload=rescue_payload,
                    ),
                    listing_case=listing_case,
                )
                cleaned_payload, normalization_diagnostics = (
                    self._normalize_payload_with_diagnostics(
                        candidate_payload,
                        result=result,
                        listing_case=listing_case,
                        rescue_source=fallback_name,
                    )
                )
                valid_data, validation_error = self._validate_payload(cleaned_payload)
                if valid_data:
                    routed_payload = await self._enrich_application_routing(
                        payload=cleaned_payload,
                        result=result,
                        crawler=crawler if fallback_name == "llm" else None,
                    )
                    cleaned_payload, normalization_diagnostics = (
                        self._normalize_payload_with_diagnostics(
                            routed_payload,
                            result=result,
                            listing_case=listing_case,
                            rescue_source=fallback_name,
                            existing_diagnostics=normalization_diagnostics,
                        )
                    )
                    valid_data, validation_error = self._validate_payload(
                        cleaned_payload
                    )
                if valid_data:
                    valid_data = self._finalize_extracted_payload(
                        payload=valid_data,
                        cleaned_payload=cleaned_payload or {},
                    )
                    extraction_method = fallback_name
                    logger.info(
                        "%s %s rescued by %s.",
                        LogTag.OK,
                        result.url,
                        fallback_name,
                    )
                    break
                rescue_errors.append(
                    f"{fallback_name}: {rescue_error or validation_error or 'unknown error'}"
                )

            if not valid_data:
                error_parts = [f"CSS Error: {css_error}"]
                error_parts.extend(rescue_errors)
                if validation_error:
                    error_parts.append(f"Validation Error: {validation_error}")
                extraction_error = " | ".join(error_parts)
                logger.error(
                    "%s %s structured extraction failed: %s",
                    LogTag.FAIL,
                    result.url,
                    validation_error or "; ".join(rescue_errors),
                )

        return (
            valid_data,
            cleaned_payload,
            normalization_diagnostics,
            extraction_method,
            extraction_error,
        )

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
        cleaned_payload: dict | None,
        normalization_diagnostics: dict[str, Any] | None,
        extraction_method: str,
        extraction_error: str | None,
        scraped_at: datetime,
        discovery_entry: ScrapeDiscoveryEntry | None = None,
        listing_result: Any | None = None,
        node_name: str = "ingest",
    ) -> str:
        listing_case = self._listing_case_payload(
            discovery_entry=discovery_entry,
            scraped_at=scraped_at,
        )
        artifact_stage = "proposed" if valid_data else "failed"
        payload = dict(valid_data or cleaned_payload or {})
        if valid_data and cleaned_payload and cleaned_payload.get("listing_case"):
            payload["listing_case"] = cleaned_payload["listing_case"]
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
            refs["raw"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="raw.json",
                data={"payload": raw_extracted},
            )
            refs["raw_extracted"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="raw_extracted.json",
                data={"data": raw_extracted},
            )
        if cleaned_payload is not None:
            refs["cleaned"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="cleaned.json",
                data={
                    "payload": cleaned_payload,
                    "diagnostics": normalization_diagnostics or {},
                },
            )
        if valid_data is not None:
            refs["extracted"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="extracted.json",
                data={"payload": valid_data},
            )
        if extraction_error:
            refs["validation_error"] = self.data_manager.write_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name=node_name,
                stage=artifact_stage,
                filename="validation_error.json",
                data={
                    "job_id": job_id,
                    "url": result.url,
                    "extraction_method": extraction_method,
                    "error": extraction_error,
                    "has_valid_data": valid_data is not None,
                },
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
                discovery_entry.listing_snippet if discovery_entry else None
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
                discovery_entry.model_extra.get("listing_case_html")
                if discovery_entry and discovery_entry.model_extra
                else None
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
                discovery_entry.model_extra.get("listing_case_cleaned_html")
                if discovery_entry and discovery_entry.model_extra
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
        crawler: AsyncWebCrawler | None = None,
        discovery_entries: dict[str, ScrapeDiscoveryEntry] | None = None,
        listing_result: Any | None = None,
        node_name: str = "ingest",
    ) -> list[str]:
        ingested_job_ids: list[str] = []
        for result in results:
            discovery_entry = (discovery_entries or {}).get(result.url)
            job_id = (
                discovery_entry.job_id
                if discovery_entry
                else self.extract_job_id(result.url)
            )
            if not result.success:
                logger.error("%s %s: %s", LogTag.FAIL, job_id, result.error_message)
                continue
            scraped_at = _now_utc()
            (
                valid_data,
                cleaned_payload,
                normalization_diagnostics,
                extraction_method,
                extraction_error,
            ) = await self._extract_payload(
                result,
                crawler=crawler,
                discovery_entry=discovery_entry,
                scraped_at=scraped_at,
            )
            self._persist_result(
                job_id=job_id,
                result=result,
                valid_data=valid_data,
                cleaned_payload=cleaned_payload,
                normalization_diagnostics=normalization_diagnostics,
                extraction_method=extraction_method,
                extraction_error=extraction_error,
                scraped_at=scraped_at,
                discovery_entry=discovery_entry,
                listing_result=listing_result,
                node_name=node_name,
            )
            if valid_data:
                ingested_job_ids.append(job_id)
        return ingested_job_ids

    def _cross_portal_seed_contracts(
        self,
        ingested_job_ids: Iterable[str],
    ) -> list[DiscoverySourceContract]:
        portal = getattr(self, "portal", None)
        source_host = _normalized_hostname(getattr(portal, "base_url", None))
        if not source_host:
            return []

        contracts: list[DiscoverySourceContract] = []
        seen_source_names: set[str] = set()
        for job_id in ingested_job_ids:
            state = self.data_manager.read_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name="ingest",
                stage="proposed",
                filename="state.json",
            )
            application_url = _normalize_application_url(state.get("application_url"))
            if not application_url:
                continue
            company_domain = _normalized_hostname(application_url)
            if not company_domain or company_domain == source_host:
                continue
            if state.get("application_method") not in {"direct_url", "onsite"}:
                continue
            contract = _cross_portal_seed_contract(
                company_domain=company_domain,
                seed_url=application_url,
                upstream_source=self.source_name,
                upstream_job_id=job_id,
            )
            if contract.source_name in seen_source_names:
                continue
            seen_source_names.add(contract.source_name)
            contracts.append(contract)
        return contracts

    async def _run_cross_portal_discovery(
        self,
        *,
        crawler: AsyncWebCrawler,
        ingested_job_ids: list[str],
        limit: int | None,
    ) -> list[str]:
        discovered_job_ids: list[str] = []
        for contract in self._cross_portal_seed_contracts(ingested_job_ids):
            adapter = _CompanyPortalAdapter(
                data_manager=self.data_manager,
                source_contract=contract,
            )
            already_scraped: list[str] = []
            source_root = self.data_manager.source_root(adapter.source_name)
            if source_root.exists():
                already_scraped = sorted(
                    path.name
                    for path in source_root.iterdir()
                    if path.is_dir()
                    and self.data_manager.has_ingested_job(
                        adapter.source_name, path.name
                    )
                )
            discovered_job_ids.extend(
                await adapter.discover_from_seed_urls(
                    crawler,
                    seed_urls=[contract.seed_url] if contract.seed_url else [],
                    already_scraped=already_scraped,
                    limit=limit,
                )
            )
        return discovered_job_ids

    async def run(
        self,
        already_scraped: list[str],
        save_html: bool = False,
        motor: MotorProvider | None = None,
        **kwargs,
    ) -> list[str]:
        """Discover jobs from a source and ingest them canonically."""
        interactive = kwargs.get("interactive", False)
        search_url = None
        
        if interactive and motor:
            logger.info("%s Performing interactive UI discovery for %s", LogTag.FAST, self.source_name)
            try:
                search_url = await self.run_interactive_discovery(motor, **kwargs)
            except Exception as exc:
                logger.error("%s Interactive discovery failed: %s. Falling back to URL.", LogTag.WARN, exc)
        
        if not search_url:
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
            links_to_crawl: list[ScrapeDiscoveryEntry] = []
            for entry in discovery_entries:
                url = entry.url
                job_id = entry.job_id
                if drop_repeated and job_id in already_scraped:
                    continue
                links_to_crawl.append(entry)

            if not links_to_crawl:
                logger.info("%s No new job postings.", LogTag.SKIP)
                return []

            limit = kwargs.get("limit")
            if limit:
                links_to_crawl = links_to_crawl[:limit]

            crawl_urls = [entry.url for entry in links_to_crawl]
            schema = await self.get_fast_schema(
                crawler,
                crawl_urls[0],
                candidate_urls=crawl_urls,
            )
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
            ingested_job_ids = await self._process_results(
                results=results,
                crawler=crawler,
                discovery_entries={entry.url: entry for entry in links_to_crawl},
                listing_result=listing_result,
            )
            ingested_job_ids.extend(
                await self._run_cross_portal_discovery(
                    crawler=crawler,
                    ingested_job_ids=ingested_job_ids,
                    limit=limit,
                )
            )
            return ingested_job_ids

    async def fetch_job(self, url: str, *, save_html: bool = False) -> str:
        """Fetch and ingest a single explicit job URL with transient error retry."""
        async with AsyncWebCrawler(config=self.get_browser_config()) as crawler:
            schema = await self.get_fast_schema(crawler, url)
            run_config = self.get_base_crawl_config()
            if schema:
                run_config.extraction_strategy = JsonCssExtractionStrategy(schema)
            result = await self._retry_crawl(crawler, url, run_config)
            if not result or not result.success:
                raise RuntimeError(
                    f"Failed to fetch job at {url}: {result.error_message if result else 'no result'}"
                )
            ingested_job_ids = await self._process_results(
                results=[result],
                crawler=crawler,
            )
        if not ingested_job_ids:
            raise RuntimeError(f"Job fetch produced no ingested artifact for {url}")
        return ingested_job_ids[0]


class _CompanyPortalAdapter(SmartScraperAdapter):
    """Generic cross-portal adapter for ATS and careers domains discovered from apply links."""

    def __init__(
        self,
        *,
        data_manager: DataManager,
        source_contract: DiscoverySourceContract,
    ) -> None:
        super().__init__(data_manager)
        self._source_contract = source_contract
        self._company_domain = source_contract.company_domain or ""

    @property
    def source_name(self) -> str:
        return self._source_contract.source_name

    @property
    def supported_params(self) -> list[str]:
        return []

    def get_search_url(self, **kwargs) -> str:
        raise NotImplementedError(
            "Company-domain discovery is seeded from application URLs."
        )

    def extract_job_id(self, url: str) -> str:
        return _generic_job_id(url)

    def extract_links(self, crawl_result: Any) -> list[ScrapeDiscoveryEntry]:
        entries: list[ScrapeDiscoveryEntry] = []
        seen_urls: set[str] = set()
        all_links = crawl_result.links.get("internal", []) + crawl_result.links.get(
            "external", []
        )
        for link in all_links:
            href = _normalize_application_url(link.get("href"))
            if not href or href in seen_urls:
                continue
            if not _same_domain_scope(href, self._company_domain):
                continue
            text = _clean_text(
                link.get("text") or link.get("title") or link.get("aria_label")
            )
            if not _job_url_hints(href, text=text):
                continue
            seen_urls.add(href)
            entries.append(
                ScrapeDiscoveryEntry(
                    url=href,
                    job_id=self.extract_job_id(href),
                    listing_position=len(entries),
                    listing_snippet=text,
                    listing_data={"job_title": text} if text else {},
                    listing_link=link,
                    source_contract=self.discovery_source_contract(),
                    source_metadata={
                        "company_domain": self._company_domain,
                        "seed_url": self._source_contract.seed_url,
                        "upstream_source": self._source_contract.upstream_source,
                        "upstream_job_id": self._source_contract.upstream_job_id,
                    },
                )
            )
        return entries

    def get_llm_instructions(self) -> str:
        return (
            "Extract from a company ATS or careers page. "
            "Treat the current page as the primary job detail page, ignore related jobs or recommendation widgets, "
            "and detect the primary language as an ISO 639-1 code."
        )

    def discovery_source_contract(self) -> DiscoverySourceContract:
        return self._source_contract

    async def discover_from_seed_urls(
        self,
        crawler: AsyncWebCrawler,
        *,
        seed_urls: list[str],
        already_scraped: list[str],
        limit: int | None,
    ) -> list[str]:
        if not seed_urls:
            return []

        links_to_crawl: list[ScrapeDiscoveryEntry] = []
        seen_urls: set[str] = set()
        for seed_url in seed_urls:
            seed_entry = ScrapeDiscoveryEntry(
                url=seed_url,
                job_id=self.extract_job_id(seed_url),
                search_url=seed_url,
                source_contract=self.discovery_source_contract(),
                source_metadata={
                    "company_domain": self._company_domain,
                    "seed_url": seed_url,
                    "upstream_source": self._source_contract.upstream_source,
                    "upstream_job_id": self._source_contract.upstream_job_id,
                },
            )
            if seed_entry.job_id not in already_scraped:
                links_to_crawl.append(seed_entry)
                seen_urls.add(seed_entry.url)

            listing_result = await crawler.arun(
                url=seed_url,
                config=self.get_base_crawl_config(),
            )
            if not listing_result.success:
                logger.warning(
                    "%s Company discovery seed failed for %s: %s",
                    LogTag.WARN,
                    seed_url,
                    listing_result.error_message,
                )
                continue

            for entry in self._normalize_discovery_entries(
                self.extract_links(listing_result),
                search_url=seed_url,
            ):
                if entry.url in seen_urls or entry.job_id in already_scraped:
                    continue
                links_to_crawl.append(entry)
                seen_urls.add(entry.url)

        if not links_to_crawl:
            return []
        if limit:
            links_to_crawl = links_to_crawl[:limit]

        crawl_urls = [entry.url for entry in links_to_crawl]
        schema = await self.get_fast_schema(
            crawler,
            crawl_urls[0],
            candidate_urls=crawl_urls,
        )
        run_config = self.get_base_crawl_config()
        if schema:
            run_config.extraction_strategy = JsonCssExtractionStrategy(schema)

        results = await crawler.arun_many(
            urls=crawl_urls,
            config=run_config,
            dispatcher=self.get_dispatcher(),
        )
        return await self._process_results(
            results=results,
            crawler=crawler,
            discovery_entries={entry.url: entry for entry in links_to_crawl},
        )
