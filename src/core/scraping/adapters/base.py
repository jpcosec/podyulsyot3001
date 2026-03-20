from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SourceCapabilities:
    source_key: str
    domains: tuple[str, ...]
    supports_listing: bool
    supports_detail: bool
    supports_apply: bool
    browser_required: bool


class SourceAdapter(Protocol):
    @property
    def capabilities(self) -> SourceCapabilities: ...

    def handles_domain(self, domain: str) -> bool: ...

    def extract_job_id(self, url: str) -> str | None: ...

    def build_detail_url(self, job_id: str) -> str | None: ...
