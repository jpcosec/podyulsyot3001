"""Shared BrowserOS runtime endpoint resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BrowserOSRuntimeConfig:
    """Resolved local BrowserOS runtime endpoints."""

    base_http_url: str
    mcp_url: str
    chat_url: str


def resolve_browseros_runtime(
    *,
    preferred_base_url: str | None = None,
) -> BrowserOSRuntimeConfig:
    """Return the canonical BrowserOS runtime endpoints for this machine.

    Resolution priority:
    1. explicit function argument
    2. `BROWSEROS_BASE_URL`
    3. stable local front door on `http://127.0.0.1:9000`
    """
    base_url = (
        preferred_base_url
        or os.environ.get("BROWSEROS_BASE_URL")
        or "http://127.0.0.1:9000"
    ).rstrip("/")
    return BrowserOSRuntimeConfig(
        base_http_url=base_url,
        mcp_url=f"{base_url}/mcp",
        chat_url=f"{base_url}/chat",
    )
