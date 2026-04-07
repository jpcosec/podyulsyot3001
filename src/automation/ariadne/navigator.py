"""Ariadne Navigator — State-Aware Replay & Recovery.

This module provides the intelligence for identifying the current 
semantic state and determining the optimal path to the mission goal. 
It enables replayers to handle deviations from the linear path.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from .exceptions import ObservationFailed, TerminalStateReached
from .models import AriadnePath, AriadnePortalMap, AriadneState, AriadneTask

logger = logging.getLogger(__name__)


class AriadneNavigator:
    """Manages semantic navigation and mission status."""

    def __init__(self, portal_map: AriadnePortalMap):
        """Initializes the navigator.
        
        Args:
            portal_map: The authoritative map for the portal.
        """
        self.portal_map = portal_map

    def find_current_state(self, observation_results: Dict[str, bool]) -> Optional[str]:
        """Identifies the current state based on presence of elements.
        
        Args:
            observation_results: Mapping of selector/text to presence boolean.
            
        Returns:
            The ID of the matched state, or None if no state matches.
        """
        for state_id, state in self.portal_map.states.items():
            if self._matches_predicate(state.presence_predicate, observation_results):
                return state_id
        return None

    def get_next_step_index(
        self, 
        current_path: AriadnePath, 
        current_step_index: int, 
        current_state_id: Optional[str]
    ) -> int:
        """Determines the index of the next step to execute.
        
        If the current state doesn't match the expected state for the next step, 
        this method attempts to find a shortcut or recovery step within the path.
        
        Args:
            current_path: The path being replayed.
            current_step_index: The index of the step just completed.
            current_state_id: The ID of the state identified after execution.
            
        Returns:
            The 1-based index of the next step to run.
        """
        next_index = current_step_index + 1
        
        if not current_state_id:
            return next_index
            
        # Check if we reached the expected state for the next step
        if next_index <= len(current_path.steps):
            expected_step = current_path.steps[next_index - 1]
            if expected_step.state_id and expected_step.state_id == current_state_id:
                return next_index
        
        # Mismatch detected: Attempt semantic jump
        for i, step in enumerate(current_path.steps):
            if step.state_id == current_state_id:
                logger.info(
                    "Semantic Recovery: Detected state '%s'. Jumping to step %s ('%s')", 
                    current_state_id, i + 1, step.name
                )
                return i + 1
                    
        return next_index

    def check_mission_status(
        self, 
        task_id: str, 
        current_state_id: str,
        page_content: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Checks if the mission goal has been achieved or terminally failed.
        
        Args:
            task_id: The ID of the task being executed.
            current_state_id: The identified current state.
            page_content: Optional text content of the page for secondary verification.
            
        Returns:
            A tuple of (is_finished, result_status).
        """
        task = self.portal_map.tasks.get(task_id)
        if not task:
            return False, None
            
        # 1. Check Explicit Success States
        if current_state_id in task.success_states:
            return True, "success"
            
        # 2. Check Explicit Failure States
        if current_state_id in task.failure_states:
            return True, "terminal_failure"
            
        # 3. Check Success Criteria (Text Match)
        if page_content and task.success_criteria:
            text_match = task.success_criteria.get("text_match")
            if text_match and text_match.lower() in page_content.lower():
                logger.info("Mission Success: Found success text '%s'", text_match)
                return True, "success"
            
        return False, None

    def _matches_predicate(self, predicate: Any, results: Dict[str, bool]) -> bool:
        """Evaluates an AriadneObserve predicate against live results."""
        presences = [results.get(t.css or t.text or "", False) for t in predicate.required_elements]
        if not presences:
            return False
            
        if predicate.logical_op == "AND":
            return all(presences)
        return any(presences)
