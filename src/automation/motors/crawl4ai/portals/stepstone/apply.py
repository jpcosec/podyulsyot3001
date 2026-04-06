"""StepStone C4AI apply translator — consumes the Ariadne Unified Map."""
from __future__ import annotations

import json
from pathlib import Path

from src.automation.ariadne.models import AriadnePortalMap
from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter


class StepStoneApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for StepStone Easy Apply using the Ariadne Semantic Layer."""

    def __init__(self, data_manager=None):
        super().__init__(data_manager)
        map_path = Path(__file__).parent.parent.parent.parent.parent / "portals" / "stepstone" / "maps" / "easy_apply.json"
        with open(map_path, "r") as f:
            self._map = AriadnePortalMap.model_validate(json.load(f))

    @property
    def portal_map(self) -> AriadnePortalMap:
        return self._map

    def get_session_profile_dir(self) -> Path:
        """Return the browser session profile directory for StepStone authentication persistence."""
        return Path("data/profiles/stepstone_profile")

    def get_success_text(self) -> str:
        """Return the German keyword that confirms a successful StepStone application."""
        return "Bewerbung"
