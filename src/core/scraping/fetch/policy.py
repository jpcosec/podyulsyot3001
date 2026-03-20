from __future__ import annotations

from src.core.scraping.contracts import FetchMode, UsedFetchMode


def select_initial_mode(
    preferred_mode: FetchMode, browser_required: bool
) -> UsedFetchMode:
    if preferred_mode == "http":
        return "http"
    if preferred_mode == "playwright":
        return "playwright"
    if browser_required:
        return "playwright"
    return "http"
