"""TU Berlin (Stellenticket) job portal adapter.

Handles bilingual (DE/EN) job postings and category-based filters.
"""

import re
from typing import Any, List
from src.scraper.smart_adapter import SmartScraperAdapter


class TUBerlinAdapter(SmartScraperAdapter):
    """Adapter for the Technische Universität Berlin job portal."""

    @property
    def source_name(self) -> str:
        return "tuberlin"

    @property
    def supported_params(self) -> List[str]:
        """TU Berlin supports categories and text-based job_query search."""
        return ["categories", "job_query"]

    def get_search_url(self, **kwargs) -> str:
        """Construct the TU Berlin filtered search results URL.

        Applies category filters for specific TU Berlin job types.
        """
        categories = kwargs.get("categories")
        job_query = kwargs.get("job_query") or ""
        base = f"https://www.jobs.tu-berlin.de/en/job-postings?filter%5Bfulltextsearch%5D={job_query}"
        filters = []

        mapping = {
            "wiss-mlehr": "Research assistant with teaching obligation",
            "wiss-olehr": "Research assistant without teaching obligation",
            "besch-abgwiss": "Beschäftigte*r mit abgeschl. wiss. Hochschulbildung",
            "techn-besch": "Techn. Beschäftigte*r",
            "besch-itb": "Beschäftigte*r in der IT-Betreuung",
            "besch-itsys": "Beschäftigte*r in der IT-Systemtechnik",
            "besch-prog": "Beschäftigte*r in der Programmierung",
        }

        if not categories:
            cat_list = list(mapping.keys())
        else:
            # Fixed: Validate if the key 'k' is in the categories requested by the user
            cat_list = [k for k in mapping.keys() if k in categories]

        for cat in cat_list:
            filters.append(f"filter%5Bworktype_tub%5D%5B%5D={cat}")

        return f"{base}&{'&'.join(filters)}"

    def extract_job_id(self, url: str) -> str:
        """Extract numeric job ID from ``/job-postings/{id}``."""
        match = re.search(r"/job-postings/(\d+)", url)
        return match.group(1) if match else "unknown"

    def extract_links(self, crawl_result: Any) -> List[str]:
        """Discover job posting URLs from TU Berlin listing page."""
        job_links = []
        internal_links = crawl_result.links.get("internal", [])
        for link in internal_links:
            href = link.get("href", "")
            if (
                "/job-postings/" in href
                and "apply" not in href
                and "download" not in href
            ):
                if href.startswith("/"):
                    job_links.append(f"https://www.jobs.tu-berlin.de{href}")
                elif href.startswith("https://"):
                    job_links.append(href)
        return sorted(list(set(job_links)))

    def get_llm_instructions(self) -> str:
        """TU Berlin-specific hints for the LLM rescue path."""
        return """
        You are extracting data from jobs.tu-berlin.de (Stellenticket).
        Pages can be in German or English. The job title is in the <h1>.
        The company is always 'Technische Universität Berlin' or a specific faculty/institute.
        The location is always 'Berlin' unless otherwise stated.
        The employment type can be 'full-time', 'part-time' or both.
        Responsibilities appear under 'Your responsibility' / 'Ihre Aufgaben'.
        Requirements under 'Your profile' / 'Ihr Profil'.
        The salary is usually a TV-L grade (e.g., 'Salary grade 13 TV-L Berliner Hochschulen').
        The posted date, deadline, and reference are in 'Facts' tables.
        The contact info is usually an email (mailto: link).
        Detect the primary language of the posting and return its ISO 639-1 code in the 'original_language' field (e.g. 'de' or 'en').
        Do not invent data. If a field does not exist, return it as null.
        """
