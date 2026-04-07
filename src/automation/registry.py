"""Automation Registry — Dynamic Provider and Motor Management.

This module acts as a factory for instantiating scraping and apply 
providers based on the requested source and execution backend.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Protocol, Type

from src.automation.ariadne.models import ApplyMeta
from src.automation.storage import AutomationStorage
from src.shared.log_tags import LogTag

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
        """Instantiates a scraping provider for the given source.
        
        Args:
            source: The portal identifier.
            storage: Automation storage instance.
            
        Returns:
            An instance of a SmartScraperAdapter.
        """
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
        """Instantiates an apply provider for the given source and backend.
        
        Args:
            source: The portal identifier.
            backend: The execution backend ('crawl4ai' or 'browseros').
            storage: Automation storage instance.
            profile_data: Optional candidate profile data.
            
        Returns:
            An instance of an ApplyAdapter or BrowserOSApplyProvider.
        """
        if backend == "browseros":
            from src.automation.motors.browseros.cli.backend import BrowserOSApplyProvider
            from src.automation.ariadne.models import AriadnePortalMap
            import json
            from pathlib import Path
            
            # Resolve Map
            map_root = Path(__file__).parent / "portals"
            map_path = map_root / source / "maps" / "easy_apply.json"
            if not map_path.exists():
                raise ValueError(f"No Ariadne Map found for {source} at {map_path}")
                
            with open(map_path, "r") as f:
                portal_map = AriadnePortalMap.model_validate(json.load(f))
                
            return BrowserOSApplyProvider(
                portal_map=portal_map,
                candidate_profile=profile_data,
                data_manager=storage.data_manager
            )
            
        elif backend == "crawl4ai":
            if source == "linkedin":
                from src.automation.motors.crawl4ai.portals.linkedin.apply import LinkedInApplyAdapter
                return LinkedInApplyAdapter(storage)
            elif source == "stepstone":
                from src.automation.motors.crawl4ai.portals.stepstone.apply import StepStoneApplyAdapter
                return StepStoneApplyAdapter(storage)
            elif source == "xing":
                from src.automation.motors.crawl4ai.portals.xing.apply import XingApplyAdapter
                return XingApplyAdapter(storage)
                
        raise ValueError(f"Unsupported apply source/backend combo: {source}/{backend}")
