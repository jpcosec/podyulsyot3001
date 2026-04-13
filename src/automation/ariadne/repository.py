"""Ariadne Map Repository - Infrastructure for loading portal maps."""

from __future__ import annotations

from pathlib import Path

from src.automation.ariadne.models import AriadneMap
from src.automation.ariadne._repository_loading import (
    load_map_sync,
    load_map_async,
    resolve_sync_or_async,
)


class MapRepository:
    """Handles the persistence and retrieval of Ariadne portal maps."""

    _map_cache: dict[str, AriadneMap] = {}

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent / "portals"

    def _cache_key(self, portal_name: str, map_type: str) -> str:
        return f"{portal_name}:{map_type}"

    def get_map(self, portal_name: str, map_type: str = "easy_apply") -> AriadneMap:
        """Retrieve a portal map (synchronous, uses thread pool)."""
        cache_key = self._cache_key(portal_name, map_type)
        if cache_key in self._map_cache:
            return self._map_cache[cache_key]

        if resolve_sync_or_async():
            ariadne_map = asyncio.run(
                load_map_async(self.base_dir, portal_name, map_type)
            )
        else:
            ariadne_map = load_map_sync(self.base_dir, portal_name, map_type)

        self._map_cache[cache_key] = ariadne_map
        return ariadne_map

    async def get_map_async(
        self, portal_name: str, map_type: str = "easy_apply"
    ) -> AriadneMap:
        """Retrieve a portal map asynchronously with caching."""
        cache_key = self._cache_key(portal_name, map_type)
        if cache_key in self._map_cache:
            return self._map_cache[cache_key]

        ariadne_map = await load_map_async(self.base_dir, portal_name, map_type)
        self._map_cache[cache_key] = ariadne_map
        return ariadne_map
