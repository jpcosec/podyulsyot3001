"""XING C4AI scrape translator — consumes XING_SCRAPE portal intent."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from src.automation.ariadne.models import ScrapePortalDefinition
from src.automation.motors.crawl4ai.contracts import ScrapeDiscoveryEntry
from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter

XING_SCRAPE = ScrapePortalDefinition(
    source_name="xing",
    base_url="https://www.xing.com",
    supported_params=["job_query", "city", "max_days"],
    job_id_pattern=r"-(\d+)(?:[?#]|$)",
)


class XingAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for XING."""

    portal = XING_SCRAPE

    @property
    def source_name(self) -> str:
        """Portal identifier for XING."""
        return self.portal.source_name

    @property
    def supported_params(self) -> list[str]:
        """Search parameters supported by the XING search URL builder."""
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        """Extract the numeric job ID from a XING detail URL using the portal pattern."""
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
        """Build a XING job search URL. Accepts job_query, city, max_days. Maps max_days to XING's numeric date filter (1/7/14/30 days)."""
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

    def extract_links(self, crawl_result: Any) -> list[ScrapeDiscoveryEntry]:
        """Return structured XING discovery entries parsed from listing HTML."""
        html = crawl_result.cleaned_html or getattr(crawl_result, "html", "")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        job_links: list[ScrapeDiscoveryEntry] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"-(\d+)$", href) and "xing.com/jobs/" in href:
                if href in seen:
                    continue
                seen.add(href)
                teaser_text = a.get_text(" ", strip=True) or None
                job_links.append(
                    ScrapeDiscoveryEntry(
                        url=href,
                        job_id=self.extract_job_id(href),
                        listing_position=len(job_links),
                        listing_snippet=teaser_text,
                        listing_data={"job_title": teaser_text} if teaser_text else {},
                        listing_link={
                            "href": href,
                            "title": a.get("title"),
                            "aria_label": a.get("aria-label"),
                        },
                        source_metadata={
                            "anchor_title": a.get("title"),
                            "anchor_aria_label": a.get("aria-label"),
                        },
                    )
                )
        return job_links

    def get_llm_instructions(self) -> str:
        """LLM extraction hints for XING job detail pages."""
        return (
            "Extract from xing.com. Job title is in the <h1>. "
            "Salary and remote policy may appear in a facts sidebar. "
            "Detect the primary language and return its ISO 639-1 code."
        )
