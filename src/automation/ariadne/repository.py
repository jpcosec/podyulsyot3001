"""Ariadne Map Repository — Infrastructure for loading portal maps."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.automation.ariadne.models import AriadneMap


class MapRepository:
    """Handles the persistence and retrieval of Ariadne portal maps."""

    _map_cache: dict[str, AriadneMap] = {}

    def __init__(self, base_dir: Path | str | None = None) -> None:
        # Default to src/automation/portals/
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent / "portals"

    def _cache_key(self, portal_name: str, map_type: str) -> str:
        return f"{portal_name}:{map_type}"

    def get_map(self, portal_name: str, map_type: str = "easy_apply") -> AriadneMap:
        """Retrieve a portal map by name and type.

        Args:
            portal_name: Name of the portal (e.g., 'linkedin').
            map_type: Type of map (default: 'easy_apply').

        Returns:
            The validated AriadneMap.

        Raises:
            FileNotFoundError: If the map JSON does not exist.
        """
        cache_key = self._cache_key(portal_name, map_type)
        if cache_key in self._map_cache:
            return self._map_cache[cache_key]
        return asyncio.get_event_loop().run_until_complete(
            self.get_map_async(portal_name, map_type)
        )

    async def get_map_async(
        self, portal_name: str, map_type: str = "easy_apply"
    ) -> AriadneMap:
        """Retrieve a portal map asynchronously with caching.

        Args:
            portal_name: Name of the portal (e.g., 'linkedin').
            map_type: Type of map (default: 'easy_apply').

        Returns:
            The validated AriadneMap.

        Raises:
            FileNotFoundError: If the map JSON does not exist.
        """
        cache_key = self._cache_key(portal_name, map_type)
        if cache_key in self._map_cache:
            return self._map_cache[cache_key]

        ariadne_map = await asyncio.to_thread(
            self._load_map_sync, portal_name, map_type
        )
        self._map_cache[cache_key] = ariadne_map
        return ariadne_map

    def _load_map_sync(self, portal_name: str, map_type: str) -> AriadneMap:
        """Load map from disk synchronously (runs in thread pool)."""
        map_path = self.base_dir / portal_name / "maps" / f"{map_type}.json"
        if not map_path.exists():
            raise FileNotFoundError(
                f"Ariadne Map not found for '{portal_name}' (type: {map_type}) at {map_path}"
            )

        with open(map_path, "r", encoding="utf-8") as f:
            return AriadneMap.model_validate(json.load(f))
