from __future__ import annotations

import importlib
import os
import time
from pathlib import Path

from src.core.scraping.fetch.base import FetchResult
from src.core.tools.errors import ToolDependencyError, ToolFailureError

DEFAULT_BOT_PROFILE_DIR = Path("data/bot_profile")


class PlaywrightFetcher:
    def fetch(
        self,
        url: str,
        timeout_seconds: float,
        error_screenshot_path: Path | None = None,
    ) -> FetchResult:
        sync_api = self._load_sync_api()
        started = time.perf_counter()
        headless = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
        user_data_dir = self._resolve_user_data_dir()

        browser_context = None
        page = None
        resolved_url = url
        status_code: int | None = None
        content = ""

        try:
            with sync_api.sync_playwright() as playwright:
                browser_context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    headless=headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = (
                    browser_context.pages[0]
                    if getattr(browser_context, "pages", None)
                    else browser_context.new_page()
                )

                response = page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=int(timeout_seconds * 1000),
                )
                content = page.content()
                resolved_url = page.url
                status_code = response.status if response else None
        except Exception as exc:  # noqa: BLE001
            self._capture_error_screenshot(page, error_screenshot_path)
            raise ToolFailureError(f"playwright fetch failed: {url}") from exc
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    pass
            if browser_context is not None:
                try:
                    browser_context.close()
                except Exception:  # noqa: BLE001
                    pass

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

    def _resolve_user_data_dir(self) -> Path:
        configured = os.getenv("BOT_PROFILE_DIR")
        path = Path(configured) if configured else DEFAULT_BOT_PROFILE_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _capture_error_screenshot(
        self,
        page: object | None,
        error_screenshot_path: Path | None,
    ) -> None:
        if page is None or error_screenshot_path is None:
            return
        try:
            error_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot = getattr(page, "screenshot", None)
            if callable(screenshot):
                screenshot(path=str(error_screenshot_path))
        except Exception:  # noqa: BLE001
            return
