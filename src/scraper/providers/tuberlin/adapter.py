
import re
from typing import Any, Dict, List
from src.scraper.base_adapter import BaseScraperAdapter

class TUBerlinAdapter(BaseScraperAdapter):
    """Adapter for the Technische Universität Berlin job portal (Stellenticket).
    
    Handles bilingual (DE/EN) job postings and category filters.
    """

    @property
    def supported_params(self) -> List[str]:
        """TU Berlin supports categories and text-based job_query search."""
        return ["categories", "job_query"]
    
    def get_search_url(self, **kwargs) -> str:
        """Constructs the TU Berlin job portal filtered search results URL.
        
        Args:
            **kwargs: Flexible arguments including categories, city, etc.
            
        Returns:
            The filtered URL for a search results page on jobs.tu-berlin.de.
        """
        categories = kwargs.get("categories")
        job_query = kwargs.get("job_query") or ""
        # Build search URL with query parameter
        base = f"https://www.jobs.tu-berlin.de/en/job-postings?filter%5Bfulltextsearch%5D={job_query}"
        filters = []
        
        # Mapping categories to TU Berlin's filter keys
        mapping = {
            "wiss-mlehr": "Research assistant with teaching obligation",
            "wiss-olehr": "Research assistant without teaching obligation",
            "besch-abgwiss": "Beschäftigte*r mit abgeschl. wiss. Hochschulbildung",
            "techn-besch": "Techn. Beschäftigte*r",
            "besch-itb": "Beschäftigte*r in der IT-Betreuung",
            "besch-itsys": "Beschäftigte*r in der IT-Systemtechnik",
            "besch-prog": "Beschäftigte*r in der Programmierung"
        }
        
        # If no categories provided, we use the full set our user requested
        if not categories:
            cat_list = list(mapping.keys())
        else:
            cat_list = [k for k, v in mapping.items() if any(c in v for c in categories)]
        
        for cat in cat_list:
            filters.append(f"filter%5Bworktype_tub%5D%5B%5D={cat}")
            
        return f"{base}&{'&'.join(filters)}"

    def get_extraction_schema(self) -> Dict[str, Any]:
        """Returns the JSON/CSS schema for TU Berlin job detail extraction.
        
        Includes mappings for job title, publication date, salary, reference 
        numbers, and contact emails (searching in both DE and EN versions).
        
        Returns:
            A dictionary containing the schema configuration for AsyncWebCrawler.
        """
        return {
            "name": "TU Berlin Extraction",
            "baseSelector": "body", 
            "fields": [
                {"name": "job_title", "selector": "h1", "type": "text"},
                {"name": "posted_date", "selector": "div:has(> div:-soup-contains('Veröffentlicht'), > div:-soup-contains('Published')) + div", "type": "text"},
                {"name": "salary", "selector": "div:has(> div:-soup-contains('Vergütung'), > div:-soup-contains('Salary')) + div", "type": "text"},
                {"name": "reference", "selector": "div:has(> div:-soup-contains('Kennziffer'), > div:-soup-contains('Reference')) + div", "type": "text"},
                {"name": "contact_email", "selector": "a[href^='mailto:']", "type": "text"}
            ]
        }

    def extract_job_id(self, url: str) -> str:
        """Extracts the numeric job ID from a TU Berlin posting URL.
        
        Args:
            url: The full job posting URL (e.g., https://.../job-postings/202653).
            
        Returns:
            The string ID of the job posting (e.g., '202653').
        """
        match = re.search(r'/job-postings/(\d+)', url)
        return match.group(1) if match else "unknown"

    def extract_links(self, crawl_result: Any) -> List[str]:
        """Extracts job posting URLs from a TU Berlin listing page.
        
        Args:
            crawl_result: The CrawlResult from AsyncWebCrawler.
            
        Returns:
            A list of absolute job posting links.
        """
        job_links = []
        internal_links = crawl_result.links.get("internal", [])
        for link in internal_links:
            href = link.get("href", "")
            # Pattern specific to TU Berlin Stellenticket listings
            if "/job-postings/" in href and "apply" not in href and "download" not in href:
                clean_match = re.search(r'(/job-postings/\d+)', href)
                if clean_match:
                    clean_href = clean_match.group(1)
                    if clean_href.startswith("/"):
                        clean_href = f"https://www.jobs.tu-berlin.de{clean_href}"
                    job_links.append(clean_href)
        return sorted(list(set(job_links)))
