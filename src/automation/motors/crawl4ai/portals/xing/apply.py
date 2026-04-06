"""XING C4AI apply translator — consumes the Ariadne Unified Map."""
from __future__ import annotations

import json
from pathlib import Path

from src.automation.ariadne.models import AriadnePortalMap
from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter


class XingApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for XING Easy Apply using the Ariadne Semantic Layer."""

    def __init__(self, data_manager=None):
        super().__init__(data_manager)
        map_path = Path(__file__).parent.parent.parent.parent.parent / "portals" / "xing" / "maps" / "easy_apply.json"
        with open(map_path, "r") as f:
            self._map = AriadnePortalMap.model_validate(json.load(f))

    @property
    def portal_map(self) -> AriadnePortalMap:
        return self._map

    def get_session_profile_dir(self) -> Path:
        """Return the browser session profile directory for XING authentication persistence."""
        return Path("data/profiles/xing_profile")

    def get_success_text(self) -> str:
        """Return the German keyword that confirms a successful XING application."""
        return "Bewerbung"
