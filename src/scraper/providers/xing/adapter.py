"""XING job portal adapter.

Uses data-testid selectors and URL slug patterns for link discovery.
"""

import re
from typing import Any, List
from src.scraper.smart_adapter import SmartScraperAdapter


class XingAdapter(SmartScraperAdapter):
    """Adapter for XING — Germany's professional networking job portal."""

    @property
    def source_name(self) -> str:
        return "xing"

    @property
    def supported_params(self) -> List[str]:
        return ["job_query", "city", "max_days"]

    def get_search_url(self, **kwargs) -> str:
        """Build XING search URL.

        Pattern: ``https://www.xing.com/jobs/search?keywords={q}&location={city}``
        """
        query = kwargs.get("job_query", "data-scientist").replace(" ", "%20")
        city = kwargs.get("city", "berlin").replace(" ", "%20")
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

    def extract_links(self, crawl_result: Any) -> List[str]:
        """Discover job URLs using XING's ``/jobs/{slug}-{id}`` pattern."""
        job_links = []
        all_links = crawl_result.links.get("internal", [])

        for link in all_links:
            href = link.get("href", "")
            if "/jobs/" in href and re.search(r"-\d+$", href):
                if href.startswith("/"):
                    href = f"https://www.xing.com{href}"
                job_links.append(href)

        return sorted(list(set(job_links)))

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
        Do not invent data that is not in the text.
        """
