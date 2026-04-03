"""XING job portal adapter.

Uses data-testid selectors and URL slug patterns for link discovery.
"""

import re
from typing import Any, List

from bs4 import BeautifulSoup

from src.scraper.smart_adapter import SmartScraperAdapter


class XingAdapter(SmartScraperAdapter):
    """Adapter for XING — Germany's professional networking job portal."""

    @property
    def source_name(self) -> str:
        """Return the canonical provider key for XING scraping."""
        return "xing"

    @property
    def supported_params(self) -> List[str]:
        """Return the search parameters supported by the XING portal."""
        return ["job_query", "city", "max_days"]

    def get_search_url(self, **kwargs) -> str:
        """Build XING search URL.

        Pattern: ``https://www.xing.com/jobs/search?keywords={q}&location={city}``
        """
        query = (kwargs.get("job_query") or "data-scientist").replace(" ", "%20")
        city = (kwargs.get("city") or "berlin").replace(" ", "%20")
        max_days = kwargs.get("max_days")

        age_str = ""
        if max_days:
            if max_days <= 1:
                age_str = "1"
            elif max_days <= 7:
                age_str = "7"
            elif max_days <= 14:
                age_str = "14"
            else:
                age_str = "30"

        url = f"https://www.xing.com/jobs/search?keywords={query}&location={city}"
        if age_str:
            url += f"&date={age_str}"
        return url

    def extract_job_id(self, url: str) -> str:
        """Extract numeric ID from XING URL slug (e.g., ``...-1234567``)."""
        match = re.search(r"-(\d+)$", url)
        return match.group(1) if match else "unknown"

    def extract_links(self, crawl_result: Any) -> List[dict[str, Any]]:
        """Discover XING jobs with per-card listing metadata preserved."""
        html = crawl_result.cleaned_html or getattr(crawl_result, "html", "")
        if not html:
            return []

        cleaned_soup = BeautifulSoup(crawl_result.cleaned_html or html, "html.parser")
        raw_soup = BeautifulSoup(
            getattr(crawl_result, "html", "") or html, "html.parser"
        )
        raw_cards = self._raw_card_map(raw_soup)
        entries: list[dict[str, Any]] = []

        for index, card in enumerate(cleaned_soup.find_all("article")):
            link = card.find("a", href=re.compile(r"/jobs/.+-\d+$"))
            if not link:
                continue
            href = link.get("href", "")
            url = href if href.startswith("https://") else f"https://www.xing.com{href}"
            entries.append(
                {
                    "url": url,
                    "listing_position": index,
                    "listing_data": self._listing_data(card),
                    "listing_snippet": card.get_text(" ", strip=True),
                    "listing_case_cleaned_html": str(card),
                    "listing_case_html": raw_cards.get(url),
                }
            )

        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for entry in entries:
            url = entry["url"]
            if url in seen:
                continue
            seen.add(url)
            deduped.append(entry)
        return deduped

    def _raw_card_map(self, soup: BeautifulSoup) -> dict[str, str]:
        cards: dict[str, str] = {}
        for card in soup.find_all("article"):
            link = card.find("a", href=re.compile(r"/jobs/.+-\d+$"))
            if not link:
                continue
            href = link.get("href", "")
            url = href if href.startswith("https://") else f"https://www.xing.com{href}"
            cards[url] = str(card)
        return cards

    # TODO(future): _listing_data uses generated CSS class names that break silently on portal rebuilds — see plan_docs/issues/scraper/scraper_fragility.md
    def _listing_data(self, card: BeautifulSoup) -> dict[str, Any]:
        title = card.find("h2")
        company = card.find(class_=re.compile("Company"))
        location_node = card.find(class_=re.compile("multi-location-display"))
        markers = [
            node.get_text(" ", strip=True)
            for node in card.select("span.marker-styles__Text-sc-8295785a-2")
        ]
        publication = card.find(class_=re.compile("PublicationDate")) or card.find(
            "time"
        )

        salary = None
        employment_type = None
        for marker in markers:
            if not marker:
                continue
            lowered = marker.lower()
            if any(
                skip in lowered
                for skip in [
                    "early applicant",
                    "external job ad",
                    "posted by a partner",
                ]
            ):
                continue
            if any(token in marker for token in ["€", "$", "TV-L"]):
                salary = marker
            elif employment_type is None:
                employment_type = marker

        return {
            "job_title": title.get_text(" ", strip=True) if title else None,
            "company_name": company.get_text(" ", strip=True) if company else None,
            "location": location_node.get_text(" ", strip=True)
            if location_node
            else None,
            "employment_type": employment_type,
            "salary": salary,
            "posted_date": publication.get_text(" ", strip=True)
            if publication
            else None,
        }

    def get_llm_instructions(self) -> str:
        """XING-specific hints for the LLM rescue path."""
        return """
        You are extracting data from XING.com.
        XING presents postings in English and German. The title is usually the first <h1>.
        The company appears as 'Sapient GmbH' or similar, followed by the sector ('Consulting').
        The location and employment type are in the header (Full-time, On-site, etc.).
        The salary is a XING estimate (e.g., '€70,000 – €91,500 (XING estimate)').
        Responsibilities are usually under 'Your Impact' or 'Deine Aufgaben'.
        Requirements under 'Skills & Experience' or 'Dein Profil'.
        If benefits appear under 'Additional Information', extract them there.
        Capture how the candidate is expected to apply: email, company portal, external portal, or a direct application action if the page states it.
        Detect the primary language of the posting and return its ISO 639-1 code in the 'original_language' field (e.g. 'de' or 'en').
        Do not invent data that is not in the text.
        """

    def get_schema_generation_hints(self) -> str:
        """Return provider-specific hints for CSS schema generation."""
        return (
            "On XING, ignore the 'Similar jobs' section entirely. "
            "Do not use selectors from teaser cards with classes containing "
            "'job-teaser', 'similar-jobs', or 'sticky-header'. "
            "The primary posting lives under the job details content area with the title, intro, highlights, and description modules."
        )
