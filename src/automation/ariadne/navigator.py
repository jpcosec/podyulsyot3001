"""Ariadne Navigator — State-Aware Replay & Recovery.

Provides the logic for identifying the current semantic state and 
determining the optimal path to the mission goal.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from .exceptions import ObservationFailed, TerminalStateReached
from .models import AriadnePath, AriadnePortalMap, AriadneState, AriadneTask

logger = logging.getLogger(__name__)


class AriadneNavigator:
    """Manages semantic navigation and state transitions."""

    def __init__(self, portal_map: AriadnePortalMap):
        self.portal_map = portal_map

    def find_current_state(self, observation_results: dict[str, bool]) -> Optional[str]:
        """Identifies the current state based on a map of present CSS/Text elements.
        
        Args:
            observation_results: Mapping of selector -> presence_bool.
        """
        for state_id, state in self.portal_map.states.items():
            if self._matches_predicate(state.presence_predicate, observation_results):
                return state_id
        return None

    def get_next_step_index(self, current_path: AriadnePath, current_step_index: int, current_state_id: Optional[str]) -> int:
        """Determines the next step to execute.
        
        If current_state_id is provided and doesn't match the expected state 
        for the next step, it attempts to find a shortcut or recovery path.
        """
        # Linear default
        next_index = current_step_index + 1
        
        if not current_state_id:
            return next_index
            
        # Semantic Check: Are we where we expected to be?
        expected_step = current_path.steps[current_step_index - 1] if current_step_index <= len(current_path.steps) else None
        
        if expected_step and expected_step.state_id and expected_step.state_id != current_state_id:
            logger.warning(
                "State Mismatch: Expected '%s', but currently in '%s'. Attempting semantic recovery.",
                expected_step.state_id, current_state_id
            )
            # Find the step that corresponds to this state
            for i, step in enumerate(current_path.steps):
                if step.state_id == current_state_id:
                    logger.info("Semantic Recovery: Jumping to step %s ('%s')", i + 1, step.name)
                    return i + 1
                    
        return next_index

    def check_mission_status(self, task_id: str, current_state_id: str) -> Tuple[bool, Optional[str]]:
        """Checks if the mission has succeeded or terminally failed.
        
        Returns:
            (is_finished, result_status)
        """
        task = self.portal_map.tasks.get(task_id)
        if not task:
            return False, None
            
        if current_state_id in task.success_states:
            return True, "success"
            
        if current_state_id in task.failure_states:
            return True, "terminal_failure"
            
        return False, None

    def _matches_predicate(self, predicate, results: dict[str, bool]) -> bool:
        """Evaluates an AriadneObserve predicate against live results."""
        presences = [results.get(t.css or t.text or "", False) for t in predicate.required_elements]
        if not presences:
            return False
            
        if predicate.logical_op == "AND":
            return all(presences)
        return any(presences)
