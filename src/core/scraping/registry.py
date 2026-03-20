from __future__ import annotations

import re
from urllib.parse import urlparse

from src.core.scraping.adapters import StepStoneAdapter
from src.core.scraping.adapters.base import SourceAdapter, SourceCapabilities
from src.core.scraping.adapters.generic import GenericAdapter

TU_BERLIN_ID_PATTERN = re.compile(r"/(?:[a-z]{2}/)?job-postings/(\d+)(?:[/?#]|$)")


class TuBerlinAdapter:
    capabilities = SourceCapabilities(
        source_key="tu_berlin",
        domains=("jobs.tu-berlin.de",),
        supports_listing=True,
        supports_detail=True,
        supports_apply=False,
        browser_required=False,
    )

    def handles_domain(self, domain: str) -> bool:
        return domain.endswith("jobs.tu-berlin.de")

    def extract_job_id(self, url: str) -> str | None:
        path = urlparse(url).path
        match = TU_BERLIN_ID_PATTERN.search(path)
        if match:
            return match.group(1)
        return None

    def build_detail_url(self, job_id: str) -> str | None:
        if not job_id.isdigit():
            return None
        return f"https://www.jobs.tu-berlin.de/en/job-postings/{job_id}"


class ScrapingRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, SourceAdapter] = {}
        self._generic = GenericAdapter()

    def register(self, adapter: SourceAdapter) -> None:
        key = adapter.capabilities.source_key
        self._adapters[key] = adapter

    def resolve(self, source: str | None, url: str) -> SourceAdapter:
        if source and source in self._adapters:
            return self._adapters[source]

        domain = (urlparse(url).hostname or "").lower()
        for adapter in self._adapters.values():
            if adapter.handles_domain(domain):
                return adapter

        return self._generic


_registry: ScrapingRegistry | None = None


def get_scraping_registry() -> ScrapingRegistry:
    global _registry
    if _registry is None:
        _registry = ScrapingRegistry()
        _registry.register(StepStoneAdapter())
        _registry.register(TuBerlinAdapter())
    return _registry
