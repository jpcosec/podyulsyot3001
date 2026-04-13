"""Ariadne Map Repository - Backwards compatibility shim."""

from __future__ import annotations

import warnings
from pathlib import Path

from src.automation.ariadne.models import AriadneMap


class MapRepository:
    """DEPRECATED: Use Labyrinth.load_from_db or AriadneThread.load_from_db instead.

    This class remains as a shim during the OOP Phase 0.5 refactor.
    """

    def __init__(self, base_dir: Path | str | None = None) -> None:
        warnings.warn(
            "MapRepository is deprecated. Use Labyrinth/AriadneThread cognition classes.",
            DeprecationWarning,
            stacklevel=2
        )
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent / "portals"

    async def get_map_async(
        self, portal_name: str, map_type: str = "easy_apply"
    ) -> AriadneMap:
        """Shim for get_map_async using Labyrinth's loader."""
        from src.automation.ariadne.core.cognition.labyrinth import Labyrinth
        lab = await Labyrinth.load_from_db(
            portal_name=portal_name,
            map_type=map_type,
            base_dir=self.base_dir.parent # Labyrinth expects parent of portals/portal_name
        )
        return lab.ariadne_map

    def get_map(self, portal_name: str, map_type: str = "easy_apply") -> AriadneMap:
        """Shim for get_map (synchronous)."""
        import asyncio
        return asyncio.run(self.get_map_async(portal_name, map_type))
