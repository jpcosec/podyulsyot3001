from __future__ import annotations

from pathlib import Path

import pytest

from src.core.scraping.fetch.playwright_fetcher import PlaywrightFetcher
from src.core.tools.errors import ToolFailureError


class _FakePage:
    def __init__(self) -> None:
        self.url = "https://example.org"
        self.closed = False
        self.screenshot_calls: list[str] = []

    def goto(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    def content(self) -> str:
        return ""

    def screenshot(self, *, path: str) -> None:
        self.screenshot_calls.append(path)
        Path(path).write_text("png", encoding="utf-8")

    def close(self) -> None:
        self.closed = True


class _FakeBrowserContext:
    def __init__(self, page: _FakePage) -> None:
        self.pages = [page]
        self.closed = False

    def new_page(self) -> _FakePage:
        return self.pages[0]

    def close(self) -> None:
        self.closed = True


class _FakeChromium:
    def __init__(self, context: _FakeBrowserContext) -> None:
        self.context = context
        self.user_data_dir: str | None = None

    def launch_persistent_context(self, *, user_data_dir: str, **_kwargs):
        self.user_data_dir = user_data_dir
        return self.context


class _FakePlaywrightManager:
    def __init__(self, chromium: _FakeChromium) -> None:
        self.chromium = chromium

    def sync_playwright(self):
        manager = self

        class _ContextManager:
            def __enter__(self_inner):
                return manager

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _ContextManager()


def test_playwright_fetcher_uses_persistent_profile_and_saves_screenshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = _FakePage()
    browser_context = _FakeBrowserContext(page)
    chromium = _FakeChromium(browser_context)
    sync_api = _FakePlaywrightManager(chromium)
    bot_profile = tmp_path / "bot_profile"
    screenshot_path = tmp_path / "trace" / "error_screenshot.png"

    monkeypatch.setenv("BOT_PROFILE_DIR", str(bot_profile))
    monkeypatch.setattr(PlaywrightFetcher, "_load_sync_api", lambda self: sync_api)

    with pytest.raises(ToolFailureError, match="playwright fetch failed"):
        PlaywrightFetcher().fetch(
            "https://example.org/job/1",
            timeout_seconds=5.0,
            error_screenshot_path=screenshot_path,
        )

    assert chromium.user_data_dir == str(bot_profile)
    assert screenshot_path.exists()
    assert page.closed is True
    assert browser_context.closed is True
