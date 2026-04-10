"""Ariadne Discovery Session — Orchestrator for interactive portal search flows."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.automation.ariadne.exceptions import (
    TerminalStateReached,
)
from src.automation.ariadne.models import AriadnePath, AriadnePortalMap
from src.automation.ariadne.motor_protocol import MotorProvider
from src.automation.ariadne.navigator import AriadneNavigator
from src.automation.storage import AutomationStorage
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class AriadneDiscoverySession:
    """Owns the discovery orchestration loop: loading search maps and executing search steps.
    """

    def __init__(
        self,
        portal_name: str,
        storage: AutomationStorage | None = None,
        recorder: Any | None = None,
    ) -> None:
        self.portal_name = portal_name
        self.storage = storage or AutomationStorage()
        self.recorder = recorder
        self._map: AriadnePortalMap | None = None

    @property
    def search_map(self) -> AriadnePortalMap:
        """Load the search map lazily from `src/automation/portals/<name>/maps/search.json`."""
        if not self._map:
            map_path = (
                Path(__file__).parent.parent
                / "portals"
                / self.portal_name
                / "maps"
                / "search.json"
            )
            if not map_path.exists():
                raise FileNotFoundError(
                    f"Ariadne Search Map not found for '{self.portal_name}' at {map_path}"
                )
            with open(map_path) as f:
                self._map = AriadnePortalMap.model_validate(json.load(f))
        return self._map

    async def run_search(
        self,
        motor: MotorProvider,
        *,
        keywords: str,
        location: str,
        path_id: str = "standard_search",
        visible: bool = False,
    ) -> str:
        """Execute a search flow and return the final page URL.

        Args:
            motor: A MotorProvider that opens browser sessions.
            keywords: Search keywords.
            location: Search location.
            path_id: The ID of the search path to execute.
            visible: Whether to perform the search in a visible browser window.

        Returns:
            The URL of the search results page.
        """
        search_map = self.search_map
        session_id = f"discovery_{self.portal_name}_{datetime.now(timezone.utc).timestamp()}"
        
        path = search_map.paths.get(path_id)
        if not path:
            raise ValueError(f"Path '{path_id}' not found in search map for {self.portal_name}")

        # Build runtime context for placeholder resolution (e.g. {{keywords}}, {{location}})
        context = {
            "keywords": keywords,
            "location": location,
        }

        all_selectors = self._collect_selectors(search_map)
        navigator = AriadneNavigator(search_map)

        async with motor.open_session(session_id, visible=visible) as ms:
            step_index = 1
            while step_index <= len(path.steps):
                step = path.steps[step_index - 1]
                
                obs = await ms.observe(all_selectors)
                current_state = navigator.find_current_state(obs)

                finished, mission_status = navigator.check_mission_status(
                    path.task_id, current_state or ""
                )
                if finished:
                    if mission_status == "terminal_failure":
                        raise TerminalStateReached(f"Search failed: Reached failure state {current_state}")
                    break

                logger.info(
                    "%s Search Step %s/%s: %s",
                    LogTag.FAST,
                    step_index,
                    len(path.steps),
                    step.name,
                )
                
                if self.recorder:
                    self.recorder.log_event(
                        "step_start",
                        step_index=step_index,
                        step_name=step.name,
                        current_state=current_state
                    )

                # We reuse execute_step but with a simplified context
                await ms.execute_step(
                    step=step,
                    context=context,
                    is_first=(step_index == 1),
                    url=search_map.base_url if step_index == 1 else None
                )

                if self.recorder:
                    # Highlight elements that were interacted with
                    for action in step.actions:
                        if action.target and action.target.css:
                            await ms.highlight_element(action.target.css, color="green")
                    
                    self.recorder.log_event("step_complete", step_index=step_index)

                obs_after = await ms.observe(all_selectors)
                next_state = navigator.find_current_state(obs_after)
                step_index = navigator.get_next_step_index(path, step_index, next_state)

            # Final check for success
            obs_final = await ms.observe(all_selectors)
            final_state = navigator.find_current_state(obs_final)
            success, _ = navigator.check_mission_status(path.task_id, final_state or "")
            
            if not success:
                logger.warning("%s Search finished but success state not confirmed.", LogTag.WARN)

            # Get the results page URL
            try:
                final_url = await ms.evaluate_script("window.location.href")
            except Exception:
                final_url = search_map.base_url # Fallback

            return final_url

    def _collect_selectors(self, portal_map: AriadnePortalMap) -> set[str]:
        selectors: set[str] = set()
        for state in portal_map.states.values():
            for target in state.presence_predicate.required_elements:
                if target.css:
                    selectors.add(target.css)
        return selectors
