from __future__ import annotations

from urllib.parse import urlparse

from src.core.scraping.adapters.base import SourceCapabilities


class GenericAdapter:
    capabilities = SourceCapabilities(
        source_key="generic",
        domains=(),
        supports_listing=False,
        supports_detail=True,
        supports_apply=False,
        browser_required=False,
    )

    def handles_domain(self, domain: str) -> bool:
        return bool(domain)

    def extract_job_id(self, url: str) -> str | None:
        # TODO: for non-job-board URLs (e.g. university admission pages), the last
        # path segment produces ugly IDs like "-1345808913953.html". Consider
        # accepting an explicit job_id override at the call site instead of
        # deriving it from the URL path.
        path = urlparse(url).path.strip("/")
        if not path:
            return None
        tail = path.split("/")[-1]
        return tail or None

    def build_detail_url(self, job_id: str) -> str | None:
        _ = job_id
        return None
