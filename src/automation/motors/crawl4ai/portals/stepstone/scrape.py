"""StepStone C4AI scrape translator — consumes STEPSTONE_SCRAPE portal intent."""
from __future__ import annotations

import re
from typing import Any

from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
from src.automation.portals.stepstone.scrape import STEPSTONE_SCRAPE


class StepStoneAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for StepStone.de."""

    portal = STEPSTONE_SCRAPE

    @property
    def source_name(self) -> str:
        """Portal identifier for StepStone.de."""
        return self.portal.source_name

    @property
    def supported_params(self) -> list[str]:
        """Search parameters supported by the StepStone search URL builder."""
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        """Extract the numeric job ID from a StepStone detail URL using the portal pattern."""
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
        """Build a StepStone search URL. Accepts job_query, city, max_days. Maps max_days to StepStone age filter codes (age_1/7/14/30)."""
        query = (kwargs.get("job_query") or "data-scientist").replace(" ", "-")
        city = (kwargs.get("city") or "berlin").lower()
        max_days = kwargs.get("max_days")
        age_str = ""
        if max_days:
            if max_days <= 1:
                age_str = "age_1"
            elif max_days <= 7:
                age_str = "age_7"
            elif max_days <= 14:
                age_str = "age_14"
            else:
                age_str = "age_30"
        url = f"https://www.stepstone.de/jobs/{query}/in-{city}"
        if age_str:
            url += f"?ag={age_str}"
        return url

    def extract_links(self, crawl_result: Any) -> list[str]:
        """Return deduplicated StepStone job detail URLs from the crawl result link list (matched by '-inline.html' suffix)."""
        job_links = []
        all_links = crawl_result.links.get("internal", []) + crawl_result.links.get("external", [])
        for link in all_links:
            href = link.get("href", "")
            if "-inline.html" in href and "stepstone.de" in href:
                job_links.append(href)
        return list(dict.fromkeys(job_links))

    def get_llm_instructions(self) -> str:
        """LLM extraction hints for StepStone job detail pages."""
        return (
            "Extract from stepstone.de. Job title is in the <h1>. "
            "Salary often appears as a range. Remote policy may appear as 'Homeoffice'. "
            "Detect the primary language and return its ISO 639-1 code."
        )
