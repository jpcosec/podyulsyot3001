from src.core.scraping.fetch.base import FetchResult, Fetcher
from src.core.scraping.fetch.http_fetcher import HttpFetcher
from src.core.scraping.fetch.playwright_fetcher import PlaywrightFetcher

__all__ = ["Fetcher", "FetchResult", "HttpFetcher", "PlaywrightFetcher"]
