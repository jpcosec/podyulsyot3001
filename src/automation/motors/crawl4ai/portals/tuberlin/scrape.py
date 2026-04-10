"""TU Berlin C4AI scrape translator — consumes TUBERLIN_SCRAPE portal intent."""

from __future__ import annotations

import re
from typing import Any

from src.automation.ariadne.models import ScrapePortalDefinition
from src.automation.motors.crawl4ai.contracts import ScrapeDiscoveryEntry
from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter

TUBERLIN_SCRAPE = ScrapePortalDefinition(
    source_name="tuberlin",
    base_url="https://www.jobs.tu-berlin.de",
    supported_params=["categories", "job_query"],
    job_id_pattern=r"/job-postings/(\d+)",
)


class TUBerlinAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for TU Berlin (Stellenticket)."""

    portal = TUBERLIN_SCRAPE

    @property
    def source_name(self) -> str:
        """Portal identifier for TU Berlin (Stellenticket)."""
        return self.portal.source_name

    @property
    def supported_params(self) -> list[str]:
        """Search parameters supported by the TU Berlin search URL builder."""
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        """Extract the numeric job ID from a TU Berlin job posting URL using the portal pattern."""
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    async def run_interactive_discovery(self, motor: MotorProvider, **kwargs) -> str:
        """Perform search using UI interaction via AriadneDiscoverySession."""
        from src.automation.ariadne.discovery_session import AriadneDiscoverySession
        
        keywords = kwargs.get("job_query") or "Data Scientist"
        location = kwargs.get("city") or "Berlin"
        
        session = AriadneDiscoverySession(self.source_name)
        return await session.run_search(motor, keywords=keywords, location=location)

    def get_search_url(self, **kwargs) -> str:
        """Build a TU Berlin Stellenticket search URL with fulltext and category filters. Category keys map to TU Berlin Stellenticket work-type filter values."""
        categories = kwargs.get("categories")
        job_query = kwargs.get("job_query") or ""
        base = f"https://www.jobs.tu-berlin.de/en/job-postings?filter%5Bfulltextsearch%5D={job_query}"
        mapping = {
            "wiss-mlehr": "Research assistant with teaching obligation",
            "wiss-olehr": "Research assistant without teaching obligation",
            "besch-abgwiss": "Beschäftigte*r mit abgeschl. wiss. Hochschulbildung",
            "techn-besch": "Techn. Beschäftigte*r",
            "besch-itb": "Beschäftigte*r in der IT-Betreuung",
            "besch-itsys": "Beschäftigte*r in der IT-Systemtechnik",
            "besch-prog": "Beschäftigte*r in der Programmierung",
        }
        cat_list = [k for k in mapping if not categories or k in categories]
        filters = [f"filter%5Bworktype_tub%5D%5B%5D={cat}" for cat in cat_list]
        return f"{base}&{'&'.join(filters)}"

    def extract_links(self, crawl_result: Any) -> list[ScrapeDiscoveryEntry]:
        """Return structured TU Berlin discovery entries from listing links."""
        job_links: list[ScrapeDiscoveryEntry] = []
        seen_urls: set[str] = set()
        for link in crawl_result.links.get("internal", []):
            href = link.get("href", "")
            if (
                "/job-postings/" in href
                and "apply" not in href
                and "download" not in href
            ):
                if href.startswith("/"):
                    href = f"https://www.jobs.tu-berlin.de{href}"
                if not href.startswith("https://") or href in seen_urls:
                    continue
                seen_urls.add(href)
                teaser_text = (
                    link.get("text") or link.get("title") or ""
                ).strip() or None
                job_links.append(
                    ScrapeDiscoveryEntry(
                        url=href,
                        job_id=self.extract_job_id(href),
                        listing_position=len(job_links),
                        listing_snippet=teaser_text,
                        listing_data={"job_title": teaser_text} if teaser_text else {},
                        listing_link=link,
                        source_metadata={
                            "link_text": link.get("text"),
                            "link_title": link.get("title"),
                        },
                    )
                )
        return job_links

    def get_llm_instructions(self) -> str:
        """LLM extraction hints for TU Berlin Stellenticket job pages. Pages may be German or English; salary is typically a TV-L grade."""
        return (
            "Extract from jobs.tu-berlin.de (Stellenticket). Pages can be German or English. "
            "Company is always Technische Universität Berlin or a specific faculty. "
            "Salary is usually a TV-L grade. Detect the primary language ISO 639-1 code."
        )
