"""Link Hinting Capability (Set-of-Mark) for Ariadne 2.0.

This module provides the implementation for injecting alphanumeric overlays
into the browser DOM to enable deterministic, hallucination-free navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from src.automation.ariadne.contracts.base import (
    AriadneTarget,
    HintingTool,
    Motor,
    ScriptCommand,
)


class HintingToolImpl(HintingTool):
    """Inject alphanumeric overlay hints through a browser motor."""

    def __init__(self, motor: Motor):
        """Initialize the hinting tool with a script-capable motor."""
        self.motor = motor
        self._hint_map: Dict[str, Dict] = {}
        self._js_path = Path(__file__).parent / "hinting.js"

    async def inject_hints(self) -> Dict[str, str]:
        """Inject DOM hints and return the hint-to-selector mapping."""
        if not self._js_path.exists():
            raise FileNotFoundError(f"Hinting JS script not found at {self._js_path}")

        script = self._js_path.read_text()
        command = ScriptCommand(script=script)
        result = await self.motor.act(command)

        if result.status != "success":
            error_msg = result.error or "Unknown error"
            raise RuntimeError(f"Failed to inject hints: {error_msg}")

        self._hint_map = result.extracted_data.get("hint_map", {})
        return {hint: data["selector"] for hint, data in self._hint_map.items()}

    async def resolve_hint(self, hint: str) -> Optional[AriadneTarget]:
        """Resolve a hint token back into an Ariadne target."""
        data = self._hint_map.get(hint.upper())
        if not data:
            return None

        return AriadneTarget(
            hint=hint.upper(),
            css=data.get("selector"),
            text=data.get("text"),
            vision=data.get("rect"),
        )
