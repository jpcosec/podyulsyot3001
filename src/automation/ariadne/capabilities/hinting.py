"""Link Hinting Capability (Set-of-Mark) for Ariadne 2.0.

This module provides the implementation for injecting alphanumeric overlays
into the browser DOM to enable deterministic, hallucination-free navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from src.automation.ariadne.contracts.base import Executor, HintingTool
from src.automation.ariadne.models import AriadneTarget, ScriptCommand


class HintingToolImpl(HintingTool):
    """
    Implementation of Link Hinting (Set-of-Mark).
    
    This capability injects alphanumeric overlays ([AA], [AB]) on all buttons,
    links, and inputs to allow LLMs to interact with elements via simple IDs.
    """

    def __init__(self, executor: Executor):
        """
        Initialize the hinting tool with a motor executor.
        
        Args:
            executor: An Ariadne Executor capable of running JavaScript via ScriptCommand.
        """
        self.executor = executor
        self._hint_map: Dict[str, Dict] = {}
        self._js_path = Path(__file__).parent / "hinting.js"

    async def inject_hints(self) -> Dict[str, str]:
        """
        Inject alphanumeric markers into the DOM.
        
        Returns:
            Dict[str, str]: A mapping of Hint ID (e.g. 'AA') to its CSS selector.
            
        Raises:
            FileNotFoundError: If the hinting.js script is missing.
            RuntimeError: If the execution of the hinting script fails.
        """
        if not self._js_path.exists():
            raise FileNotFoundError(f"Hinting JS script not found at {self._js_path}")
            
        script = self._js_path.read_text()
        
        # Execute the script via the provided executor
        # The executor is responsible for returning the script's result 
        # in the `extracted_data["hint_map"]` field of the ExecutionResult.
        command = ScriptCommand(script=script)
        result = await self.executor.execute(command)
        
        if result.status == "success":
            # Store the full metadata for resolution later
            self._hint_map = result.extracted_data.get("hint_map", {})
            
            # Return a simplified map of hint -> selector for the caller (e.g. a Planner)
            return {hint: data["selector"] for hint, data in self._hint_map.items()}
        else:
            error_msg = result.error or "Unknown error"
            raise RuntimeError(f"Failed to inject hints: {error_msg}")

    async def resolve_hint(self, hint: str) -> Optional[AriadneTarget]:
        """
        Translate a marker (e.g. 'AA') back into a semantic target.
        
        Args:
            hint: The alphanumeric marker (case-insensitive) to resolve.
            
        Returns:
            Optional[AriadneTarget]: The resolved target with multi-strategy identification.
        """
        # Ensure we check the hint map case-insensitively if needed, 
        # but JS script generates uppercase.
        data = self._hint_map.get(hint.upper())
        if not data:
            return None
        
        return AriadneTarget(
            hint=hint.upper(),
            css=data.get("selector"),
            text=data.get("text"),
            vision=data.get("rect")
        )
