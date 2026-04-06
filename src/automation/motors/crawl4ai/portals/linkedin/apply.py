"""LinkedIn C4AI apply translator — consumes the Ariadne Unified Map."""
from __future__ import annotations

import json
from pathlib import Path

from src.automation.ariadne.models import AriadnePortalMap
from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter


class LinkedInApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for LinkedIn Easy Apply using the Ariadne Semantic Layer."""

    def __init__(self, data_manager=None):
        super().__init__(data_manager)
        map_path = Path(__file__).parent.parent.parent.parent.parent / "portals" / "linkedin" / "maps" / "easy_apply.json"
        with open(map_path, "r") as f:
            self._map = AriadnePortalMap.model_validate(json.load(f))

    @property
    def portal_map(self) -> AriadnePortalMap:
        return self._map

    def get_session_profile_dir(self) -> Path:
        """Return the browser session profile directory for LinkedIn authentication persistence."""
        return Path("data/profiles/linkedin_profile")

    def get_success_text(self) -> str:
        """Return the English keyword that confirms a successful LinkedIn Easy Apply submission."""
        return "application"
