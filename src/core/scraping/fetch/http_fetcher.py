from __future__ import annotations

import time
import urllib.request

from src.core.tools.errors import ToolFailureError
from src.core.scraping.fetch.base import FetchResult


class HttpFetcher:
    def fetch(self, url: str, timeout_seconds: float) -> FetchResult:
        started = time.perf_counter()
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # type: ignore[misc]
                payload = response.read()
                resolved_url = response.geturl()
                status_code = getattr(response, "status", None)
        except Exception as exc:  # noqa: BLE001
            raise ToolFailureError(f"http fetch failed: {url}") from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return FetchResult(
            url=url,
            resolved_url=resolved_url,
            status_code=status_code,
            content=payload.decode("utf-8", errors="replace"),
            mode="http",
            warnings=[f"http_elapsed_ms:{elapsed_ms}"],
        )
