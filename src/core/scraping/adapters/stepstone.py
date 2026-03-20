from __future__ import annotations

import re
from urllib.parse import urlparse

from src.core.scraping.adapters.base import SourceCapabilities

STEPSTONE_ID_PATTERN = re.compile(r"--(\d+)-inline\.html$")


class StepStoneAdapter:
    capabilities = SourceCapabilities(
        source_key="stepstone",
        domains=("stepstone.de",),
        supports_listing=True,
        supports_detail=True,
        supports_apply=False,
        browser_required=False,
    )

    def handles_domain(self, domain: str) -> bool:
        return domain.endswith("stepstone.de")

    def extract_job_id(self, url: str) -> str | None:
        path = urlparse(url).path
        match = STEPSTONE_ID_PATTERN.search(path)
        if match:
            return match.group(1)
        return None

    def build_detail_url(self, job_id: str) -> str | None:
        if not job_id.isdigit():
            return None
        return f"https://www.stepstone.de/stellenangebote--x--{job_id}-inline.html"
