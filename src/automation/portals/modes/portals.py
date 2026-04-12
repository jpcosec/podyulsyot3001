"""Portal-specific Ariadne Mode implementations."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.automation.ariadne.danger_contracts import ApplyDangerReport, ApplyDangerSignals
from src.automation.ariadne.models import AriadneStateDefinition, JobPosting
from src.automation.ariadne.modes.base import AriadneMode


class JsonConfigMode(AriadneMode):
    """Base class for modes that load rules from JSON configs."""

    def __init__(self, portal_name: str):
        self.portal_name = portal_name
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "configs" / f"{self.portal_name}.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        # Default implementation: pass-through
        return payload

    def inspect_danger(self, snapshot: Any) -> ApplyDangerReport:
        # Default implementation: no findings
        return ApplyDangerReport(findings=[])

    def apply_local_heuristics(
        self, state: AriadneStateDefinition
    ) -> AriadneStateDefinition:
        # Inject selectors from config into the state components
        selectors = self.config.get("selectors", {})
        for key, css in selectors.items():
            if key not in state.components:
                from src.automation.ariadne.models import AriadneTarget
                state.components[key] = AriadneTarget(css=css)
        return state


class LinkedInMode(JsonConfigMode):
    """LinkedIn-specific heuristics and cleanup."""
    url_patterns = ["linkedin.com"]

    def __init__(self):
        super().__init__("linkedin")

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        # Cleanup LinkedIn-specific location suffixes
        if payload.location:
            payload.location = payload.location.split("·")[0].strip()
        return payload


class StepStoneMode(JsonConfigMode):
    """StepStone-specific heuristics and cleanup."""
    url_patterns = ["stepstone"]

    def __init__(self):
        super().__init__("stepstone")

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        # Cleanup StepStone markers
        if payload.company_name:
            payload.company_name = payload.company_name.replace(" (m/w/d)", "").strip()
        return payload


class XingMode(JsonConfigMode):
    """Xing-specific heuristics and cleanup."""
    url_patterns = ["xing.com"]

    def __init__(self):
        super().__init__("xing")
