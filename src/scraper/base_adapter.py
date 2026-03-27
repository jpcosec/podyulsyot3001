from abc import ABC, abstractmethod
import asyncio
import os
import json
import re
from typing import Any, Dict, List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

class BaseScraperAdapter(ABC):
    """Abstract base class define the interface for all job portal scrapers.
    
    Any new source (e.g., StepStone, XING) should implement this class to 
    be compatible with the Scraper CLI.
    """

    @property
    @abstractmethod
    def supported_params(self) -> List[str]:
        """Returns the list of search parameters supported by this adapter.
        
        Example: ['categories', 'job_query', 'max_days']
        """
        pass

    @abstractmethod
    def get_search_url(self, **kwargs) -> str:
        """Constructs the filtered search results URL for the provider."""
        pass

    @abstractmethod
    def get_extraction_schema(self) -> Dict[str, Any]:
        """Returns the crawl4ai JSON/CSS schema for detail extraction."""
        pass

    @abstractmethod
    def extract_job_id(self, url: str) -> str:
        """Extracts a unique job ID from the job posting URL."""
        pass

    @abstractmethod
    def extract_links(self, crawl_result: Any) -> List[str]:
        """Extracts job posting URLs from a listing page crawl result."""
        pass

    async def run(self, already_scraped: List[str], **kwargs):
        """Standardized orchestration loop for crawling and scraping.
        
        This method is shared across all adapters to ensure consistent 
        behavior (check for duplicates, save fits, etc.).
        """
        search_url = self.get_search_url(**kwargs)
        drop_repeated = kwargs.get("drop_repeated", True)
        
        browser_config = BrowserConfig(headless=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"[*] Crawling listing: {search_url}")
            listing_result = await crawler.arun(url=search_url)
            
            if not listing_result.success:
                print(f"[!] Listing crawl failed: {listing_result.error_message}")
                return

            links = self.extract_links(listing_result)
            print(f"[*] Found {len(links)} links. Starting detail scrape...")
            
            for i, url in enumerate(links):
                job_id = self.extract_job_id(url)
                output_dir = f"data/source/{job_id}"
                
                if drop_repeated and job_id in already_scraped:
                    print(f"  [{i+1}/{len(links)}] [SKIPPED] {job_id}")
                    continue
                
                print(f"  [{i+1}/{len(links)}] Scraping {job_id}...")
                os.makedirs(output_dir, exist_ok=True)
                
                run_config = CrawlerRunConfig(
                    extraction_strategy=JsonCssExtractionStrategy(self.get_extraction_schema()),
                    cache_mode=CacheMode.BYPASS,
                )
                
                result = await crawler.arun(url=url, config=run_config)
                if result.success:
                    # Save artifacts
                    with open(os.path.join(output_dir, "raw_content.md"), "w", encoding="utf-8") as f:
                        f.write(result.markdown.raw_markdown)
                    try:
                        data = json.loads(result.extracted_content)
                        with open(os.path.join(output_dir, "extracted_data.json"), "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                    except:
                        pass
