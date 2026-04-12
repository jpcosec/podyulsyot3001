"""Portal-specific Ariadne Mode implementations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

from src.automation.ariadne.danger_contracts import (
    ApplyDangerFinding,
    ApplyDangerReport,
    ApplyDangerSignals,
)
from src.automation.ariadne.models import AriadneStateDefinition, JobPosting
from src.automation.ariadne.modes.base import AriadneMode


class JsonConfigMode(AriadneMode):
    """Base class for modes that load rules from JSON configs."""

    _config_cache: ClassVar[Dict[str, Dict[str, Any]]] = {}
    _configs_loaded: ClassVar[bool] = False

    def __init__(self, portal_name: str):
        self.portal_name = portal_name
        self.config = self.get_config(portal_name)

    @classmethod
    def preload_configs(cls) -> None:
        """Load all portal configs once before graph execution begins."""
        if cls._configs_loaded:
            return

        config_dir = Path(__file__).parent.parent / "configs"
        loaded_configs: Dict[str, Dict[str, Any]] = {}
        for config_path in config_dir.glob("*.json"):
            with config_path.open("r", encoding="utf-8") as handle:
                loaded_configs[config_path.stem] = json.load(handle)

        cls._config_cache = loaded_configs
        cls._configs_loaded = True

    @classmethod
    def get_config(cls, portal_name: str) -> Dict[str, Any]:
        """Return a cached config for the requested portal."""
        if not cls._configs_loaded:
            cls.preload_configs()
        return dict(cls._config_cache.get(portal_name, {}))

    async def normalize_job(self, payload: JobPosting) -> JobPosting:
        # Default implementation: pass-through
        return payload

    async def inspect_danger(self, snapshot: Any) -> ApplyDangerReport:
        if not isinstance(snapshot, ApplyDangerSignals):
            return ApplyDangerReport(findings=[])

        danger_config = self.get_config("danger_detection")
        text_rules = danger_config.get("text_rules", [])
        evidence = " ".join(
            part.lower()
            for part in [
                snapshot.dom_text,
                snapshot.screenshot_text,
                snapshot.current_url,
            ]
            if part
        )

        findings = []
        for rule in text_rules:
            rule_text = rule.strip().lower()
            if not rule_text or not re.search(rf"\b{re.escape(rule_text)}\b", evidence):
                continue

            findings.append(
                ApplyDangerFinding(
                    code="SECURITY_CHECK_DETECTED",
                    source="dom_text",
                    recommended_action="pause",
                    message=f"Detected security-blocking text matching '{rule}'.",
                    matched_text=rule,
                )
            )

        return ApplyDangerReport(findings=findings)

    async def apply_local_heuristics(
        self,
        state_definition: AriadneStateDefinition,
        runtime_state: Optional[Dict[str, Any]] = None,
    ) -> AriadneStateDefinition:
        # Inject selectors from config into the state components
        selectors = self.config.get("selectors", {})
        for key, css in selectors.items():
            if key not in state_definition.components:
                from src.automation.ariadne.models import AriadneTarget

                state_definition.components[key] = AriadneTarget(css=css)
        return state_definition


class LinkedInMode(JsonConfigMode):
    """LinkedIn-specific heuristics and cleanup."""

    url_patterns = ["linkedin.com"]

    def __init__(self):
        super().__init__("linkedin")

    async def normalize_job(self, payload: JobPosting) -> JobPosting:
        # Cleanup LinkedIn-specific location suffixes
        if payload.location:
            payload.location = payload.location.split("·")[0].strip()
        return payload


class StepStoneMode(JsonConfigMode):
    """StepStone-specific heuristics and cleanup."""

    url_patterns = ["stepstone"]

    def __init__(self):
        super().__init__("stepstone")

    async def normalize_job(self, payload: JobPosting) -> JobPosting:
        # Cleanup StepStone markers
        if payload.company_name:
            payload.company_name = payload.company_name.replace(" (m/w/d)", "").strip()
        return payload


class XingMode(JsonConfigMode):
    """Xing-specific heuristics and cleanup."""

    url_patterns = ["xing.com"]

    def __init__(self):
        super().__init__("xing")
