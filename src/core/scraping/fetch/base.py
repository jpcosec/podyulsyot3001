from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FetchResult:
    url: str
    resolved_url: str
    status_code: int | None
    content: str
    mode: str
    warnings: list[str]


class Fetcher(Protocol):
    def fetch(self, url: str, timeout_seconds: float) -> FetchResult: ...
