from src.core.scraping.contracts import (
    CrawlListingRequest,
    CrawlListingResult,
    ScrapeDetailRequest,
    ScrapeDetailResult,
)
from src.core.scraping.service import crawl_listing, scrape_detail

__all__ = [
    "ScrapeDetailRequest",
    "ScrapeDetailResult",
    "CrawlListingRequest",
    "CrawlListingResult",
    "scrape_detail",
    "crawl_listing",
]
