"""Ariadne Map Repository — Infrastructure for loading portal maps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.automation.ariadne.models import AriadneMap


class MapRepository:
    """Handles the persistence and retrieval of Ariadne portal maps."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        # Default to src/automation/portals/
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent / "portals"

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
        map_path = self.base_dir / portal_name / "maps" / f"{map_type}.json"
        if not map_path.exists():
            raise FileNotFoundError(
                f"Ariadne Map not found for '{portal_name}' (type: {map_type}) at {map_path}"
            )

        with open(map_path, "r", encoding="utf-8") as f:
            return AriadneMap.model_validate(json.load(f))
