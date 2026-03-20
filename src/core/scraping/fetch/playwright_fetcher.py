from __future__ import annotations

import importlib
import time

from src.core.tools.errors import ToolDependencyError, ToolFailureError
from src.core.scraping.fetch.base import FetchResult


class PlaywrightFetcher:
    def fetch(self, url: str, timeout_seconds: float) -> FetchResult:
        sync_api = self._load_sync_api()

        started = time.perf_counter()
        browser = None
        try:
            with sync_api.sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                response = page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=int(timeout_seconds * 1000),
                )
                content = page.content()
                resolved_url = page.url
                status_code = response.status if response else None
                page.close()
        except Exception as exc:  # noqa: BLE001
            raise ToolFailureError(f"playwright fetch failed: {url}") from exc
        finally:
            if browser is not None:
                browser.close()

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return FetchResult(
            url=url,
            resolved_url=resolved_url,
            status_code=status_code,
            content=content,
            mode="playwright",
            warnings=[f"playwright_elapsed_ms:{elapsed_ms}"],
        )

    def _load_sync_api(self):
        try:
            return importlib.import_module("playwright.sync_api")
        except Exception as exc:  # noqa: BLE001
            raise ToolDependencyError("playwright is not installed") from exc
