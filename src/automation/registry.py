"""Automation Registry — Dynamic Provider and Motor Management.

This module acts as a factory for instantiating scraping and apply 
providers based on the requested source and execution backend.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Protocol

from src.automation.ariadne.models import ApplyMeta
from src.automation.storage import AutomationStorage

logger = logging.getLogger(__name__)


class ApplyProvider(Protocol):
    """Protocol for apply providers to ensure consistent interface."""
    async def run(self, **kwargs: Any) -> ApplyMeta: ...
    async def setup_session(self) -> None: ...


class ScrapeProvider(Protocol):
    """Protocol for scrape providers."""
    async def run(self, **kwargs: Any) -> list[str]: ...
    @property
    def supported_params(self) -> list[str]: ...


class AutomationRegistry:
    """Central registry for discovering and building automation providers."""

    @staticmethod
    def get_scrape_provider(source: str, storage: AutomationStorage) -> ScrapeProvider:
        """Instantiates a scraping provider for the given source."""
        if source == "stepstone":
            from src.automation.motors.crawl4ai.portals.stepstone.scrape import StepStoneAdapter
            return StepStoneAdapter(storage.data_manager)
        elif source == "xing":
            from src.automation.motors.crawl4ai.portals.xing.scrape import XingAdapter
            return XingAdapter(storage.data_manager)
        elif source == "tuberlin":
            from src.automation.motors.crawl4ai.portals.tuberlin.scrape import TUBerlinAdapter
            return TUBerlinAdapter(storage.data_manager)
        
        raise ValueError(f"Unsupported scrape source: {source}")

    @staticmethod
    def get_apply_provider(
        source: str, 
        backend: str, 
        storage: AutomationStorage,
        profile_data: Optional[Dict[str, Any]] = None
    ) -> ApplyProvider:
        """Instantiates an apply provider for the given source and backend."""
        if backend == "browseros":
            from src.automation.motors.browseros.cli.backend import BrowserOSApplyProvider
            return BrowserOSApplyProvider(
                source_name=source,
                candidate_profile=profile_data,
                data_manager=storage.data_manager
            )
            
        elif backend == "crawl4ai":
            from src.automation.motors.crawl4ai.apply_engine import Crawl4AIApplyProvider
            return Crawl4AIApplyProvider(source_name=source, storage=storage)
                
        raise ValueError(f"Unsupported apply source/backend combo: {source}/{backend}")
