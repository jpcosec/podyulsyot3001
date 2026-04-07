"""BrowserOS Injection — Injecting BrowserOS into Crawl4AI.

This module provides the connection logic to ensure Crawl4AI uses the
Chromium instance managed by BrowserOS via CDP (port 9101).
"""

from __future__ import annotations

import logging
from crawl4ai import BrowserConfig

logger = logging.getLogger(__name__)

# Standard BrowserOS CDP port as defined in architecture docs
BROWSEROS_CDP_URL = "http://localhost:9101"


def get_browseros_injected_config(
    headless: bool = True,
    text_mode: bool = False
) -> BrowserConfig:
    """Returns a Crawl4AI BrowserConfig that attaches to BrowserOS.

    Args:
        headless: This flag is ignored when connecting to a remote CDP browser,
                 as BrowserOS manages its own window visibility.
        text_mode: Whether to optimize for text extraction.

    Returns:
        BrowserConfig configured with BrowserOS CDP URL.
    """
    logger.info("Injecting BrowserOS browser (CDP: %s) into motor.", BROWSEROS_CDP_URL)

    return BrowserConfig(
        browser_type="chromium",
        cdp_url=BROWSEROS_CDP_URL,
        headless=headless,
        text_mode=text_mode,
    )
