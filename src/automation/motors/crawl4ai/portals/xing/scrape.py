"""XING C4AI scrape translator — consumes XING_SCRAPE portal intent."""
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
from src.automation.portals.xing.scrape import XING_SCRAPE


class XingAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for XING."""

    portal = XING_SCRAPE

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    @property
    def supported_params(self) -> list[str]:
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
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

    def extract_links(self, crawl_result: Any) -> list[dict[str, Any]]:
        html = crawl_result.cleaned_html or getattr(crawl_result, "html", "")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        job_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"-(\d+)$", href) and "xing.com/jobs/" in href:
                job_links.append({"href": href, "text": a.get_text(strip=True)})
        seen = set()
        unique = []
        for item in job_links:
            if item["href"] not in seen:
                seen.add(item["href"])
                unique.append(item)
        return unique

    def get_llm_instructions(self) -> str:
        return (
            "Extract from xing.com. Job title is in the <h1>. "
            "Salary and remote policy may appear in a facts sidebar. "
            "Detect the primary language and return its ISO 639-1 code."
        )
