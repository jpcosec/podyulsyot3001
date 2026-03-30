"""StepStone job portal adapter.

Uses URL patterns and data-attribute selectors rescued from the legacy dev branch.
"""

import re
from typing import Any, List
from src.scraper.smart_adapter import SmartScraperAdapter


class StepStoneAdapter(SmartScraperAdapter):
    """Adapter for StepStone.de — Germany's largest commercial job portal."""

    @property
    def source_name(self) -> str:
        return "stepstone"

    @property
    def supported_params(self) -> List[str]:
        return ["job_query", "city", "max_days"]

    def get_search_url(self, **kwargs) -> str:
        """Build StepStone search URL.

        Pattern: ``https://www.stepstone.de/jobs/{query}/in-{city}?ag={age}``
        """
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

    def extract_job_id(self, url: str) -> str:
        """Extract numeric Job ID from ``stellenangebote--{id}-inline.html``."""
        match = re.search(r"--(\d+)-inline\.html", url)
        return match.group(1) if match else "unknown"

    # TODO(future): extract_links returns plain URL strings, losing listing-side metadata — see future_docs/issues/scraper_fragility.md
    def extract_links(self, crawl_result: Any) -> List[str]:
        """Discover job URLs using crawl4ai's native link discovery."""
        job_links = []
        all_links = crawl_result.links.get("internal", []) + crawl_result.links.get(
            "external", []
        )

        for link in all_links:
            href = link.get("href", "")
            if "stellenangebote--" in href and href.endswith("-inline.html"):
                clean_match = re.search(r"(/stellenangebote--.*\.html)", href)
                if clean_match:
                    full_href = clean_match.group(1)
                    if full_href.startswith("/"):
                        full_href = f"https://www.stepstone.de{full_href}"
                    job_links.append(full_href)

        return sorted(list(set(job_links)))

    def get_llm_instructions(self) -> str:
        """StepStone-specific hints for the LLM rescue path."""
        return """
        You are extracting data from StepStone.de.
        Pay close attention to the main text of the posting. Often, companies mix
        'responsibilities' (Tus tareas / Deine Aufgaben) with 'requirements' (Tu perfil / Dein Profil).
        Separate them logically.
        If the company does not specify salary or benefits, return null or an empty list, do not invent.
        The 'posted_date' field usually appears as 'vor X Tagen' or 'Erschienen: vor 1 Woche'.
        Capture how the candidate must apply when stated: email, external portal, company portal, or direct apply link.
        Detect the primary language of the posting and return its ISO 639-1 code in the 'original_language' field (e.g. 'de' or 'en').
        """
