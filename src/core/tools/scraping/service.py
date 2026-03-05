"""Scraping helpers for non-LLM bounded-nondeterministic steps."""

from __future__ import annotations

import re
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from typing import Callable

from src.core.tools.errors import ToolFailureError

JOB_LINK_RE = re.compile(r"/(?:[a-z]{2}/)?job-postings/(\d+)(?=[^0-9]|$)")
GERMAN_MARKERS = (
    " bewerbung ",
    " bewerbungsfrist ",
    " aufgaben ",
    " anforderungen ",
    " stellenausschreibung ",
)


@dataclass(frozen=True)
class ListingCrawlResult:
    discovered_ids: list[str]
    known_ids: list[str]
    new_ids: list[str]


def build_listing_page_url(base_url: str, page: int) -> str:
    """Build a deterministic listing URL with a page query parameter."""
    if re.search(r"([?&])page=\d+", base_url):
        return re.sub(r"([?&])page=\d+", rf"\1page={page}", base_url, count=1)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page}"


def fetch_html(
    url: str,
    *,
    timeout_seconds: float = 20.0,
    user_agent: str = "Mozilla/5.0",
    urlopen_fn: Callable[..., object] | None = None,
) -> str:
    """Fetch HTML content with explicit timeout control."""
    opener = urlopen_fn or urllib.request.urlopen
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with opener(request, timeout=timeout_seconds) as response:  # type: ignore[misc]
            payload = response.read()
    except Exception as exc:  # noqa: BLE001
        raise ToolFailureError(f"failed to fetch html: {url}") from exc
    return payload.decode("utf-8", errors="replace")


def extract_job_ids_from_listing_html(html: str) -> set[str]:
    """Extract numeric job ids from listing HTML."""
    return set(JOB_LINK_RE.findall(html))


def crawl_listing(
    listing_url: str,
    *,
    known_job_ids: set[str] | None = None,
    max_pages: int = 100,
    delay_seconds: float = 0.0,
    fetch_html_fn: Callable[[str], str] = fetch_html,
) -> ListingCrawlResult:
    """Crawl listing pages and return discovered/new ids."""
    known_ids = set(known_job_ids or set())
    discovered_ids: set[str] = set()
    previous_page_ids: set[str] | None = None

    for page in range(1, max_pages + 1):
        page_url = build_listing_page_url(listing_url, page)
        html = fetch_html_fn(page_url)
        page_ids = extract_job_ids_from_listing_html(html)

        if not page_ids:
            break
        if previous_page_ids is not None and page_ids == previous_page_ids:
            break

        discovered_ids.update(page_ids)
        previous_page_ids = page_ids
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    new_ids = discovered_ids - known_ids
    return ListingCrawlResult(
        discovered_ids=sorted(discovered_ids),
        known_ids=sorted(known_ids),
        new_ids=sorted(new_ids),
    )


def extract_source_text_markdown(html_content: str, *, url: str) -> str:
    """Render a compact markdown source snapshot from HTML."""
    stripped = _strip_html(html_content)
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Scraped Source Text",
        "",
        f"- URL: {url}",
        f"- Retrieved UTC: {timestamp}",
        "",
        "## Main Content",
    ]
    for raw_line in stripped.splitlines():
        line = _normalize_spaces(raw_line)
        if line:
            lines.append(line)
    lines.append("")
    return "\n".join(lines)


def detect_english_status(markdown_text: str) -> dict[str, object]:
    """Heuristic language check used by the scraping path."""
    lowered = f" {_normalize_key(markdown_text)} "
    marker_hits = sum(lowered.count(marker.strip()) for marker in GERMAN_MARKERS)
    has_umlaut = any(ch in markdown_text for ch in "äöüÄÖÜß")
    return {
        "is_english": marker_hits <= 1,
        "marker_hits": marker_hits,
        "has_umlaut": has_umlaut,
    }


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_key(text: str) -> str:
    return (
        _normalize_spaces(text)
        .lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def _strip_html(html_content: str) -> str:
    text = re.sub(r"<script.*?>.*?</script>", " ", html_content, flags=re.DOTALL)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)
    return unescape(text)
