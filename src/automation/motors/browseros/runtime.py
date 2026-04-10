"""Shared BrowserOS runtime endpoint resolution and health management."""

from __future__ import annotations

import logging
import os
import subprocess
import time
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BrowserOSRuntimeConfig:
    """Resolved local BrowserOS runtime endpoints."""

    base_http_url: str
    mcp_url: str
    chat_url: str


def resolve_browseros_appimage_path() -> str | None:
    """Return the configured BrowserOS AppImage path, if any."""
    appimage_path = os.environ.get("BROWSEROS_APPIMAGE_PATH", "").strip()
    return appimage_path or None


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


def is_runtime_ready(url: str, timeout: float = 1.0) -> bool:
    """Return whether a BrowserOS endpoint is reachable and returning 200 OK."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def ensure_browseros_running(
    runtime: BrowserOSRuntimeConfig,
    timeout_seconds: int = 30,
) -> None:
    """Ensure the BrowserOS runtime is healthy; auto-launch if possible.

    If the MCP endpoint is unreachable, this function attempts to launch
    the configured AppImage from `BROWSEROS_APPIMAGE_PATH` in the background
    and polls for readiness.
    """
    if is_runtime_ready(runtime.mcp_url):
        return

    app_path = resolve_browseros_appimage_path()
    if not app_path:
        logger.warning(
            "BrowserOS MCP unreachable at %s and BROWSEROS_APPIMAGE_PATH is not set. "
            "Cannot auto-launch.",
            runtime.mcp_url,
        )
        return

    if not os.path.exists(app_path):
        logger.warning(
            "BrowserOS MCP unreachable at %s and AppImage not found at %s. "
            "Cannot auto-launch.",
            runtime.mcp_url,
            app_path,
        )
        return

    logger.info("Launching BrowserOS AppImage at %s...", app_path)
    try:
        # Launch in a new session to detach from the parent process group
        subprocess.Popen(
            [app_path, "--no-sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        logger.error("Failed to launch BrowserOS AppImage: %s", exc)
        return

    # Poll until ready or timeout
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        if is_runtime_ready(runtime.mcp_url):
            logger.info("BrowserOS MCP is ready at %s", runtime.mcp_url)
            return
        time.sleep(1.0)

    logger.error("Timed out waiting for BrowserOS MCP at %s", runtime.mcp_url)
