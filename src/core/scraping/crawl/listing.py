from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ListingDiscovery:
    discovered_urls: list[str] = field(default_factory=list)
    discovered_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
