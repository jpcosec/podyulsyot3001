"""Ariadne Normalizer — Raw Trace to Semantic Map Conversion.

Processes raw session traces and generates draft Ariadne Maps by grouping 
related events into steps and inferring semantic states.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadnePath,
    AriadnePortalMap,
    AriadneStep,
    AriadneTarget,
)
from .trace_models import AriadneSessionTrace, RawTraceEvent

logger = logging.getLogger(__name__)


class AriadneNormalizer:
    """Heuristic-based normalizer for converting traces to maps."""

    def normalize(self, trace: AriadneSessionTrace) -> AriadnePortalMap:
        """Main entry point for normalization."""
        logger.info("Normalizing trace for portal: %s", trace.portal_name)
        
        # 1. Group events into steps (Heuristic: group by navigation or delay)
        steps = self._infer_steps(trace.events)
        
        # 2. Create a default path
        path = AriadnePath(
            id="recorded_flow",
            task_id="inferred_task",
            steps=steps
        )
        
        # 3. Assemble map
        portal_map = AriadnePortalMap(
            portal_name=trace.portal_name,
            base_url=trace.events[0].page_url or "",
            states={},  # TODO: Implement state inference logic
            tasks={},
            paths={"recorded_flow": path}
        )
        
        return portal_map

    def _infer_steps(self, events: List[RawTraceEvent]) -> List[AriadneStep]:
        """Group raw events into sequential AriadneSteps."""
        steps: List[AriadneStep] = []
        current_actions: List[AriadneAction] = []
        step_counter = 1

        for event in events:
            intent = self._map_event_to_intent(event)
            if not intent:
                continue

            action = AriadneAction(
                intent=intent,
                target=AriadneTarget(css=event.selector, text=event.page_title), # Placeholder text
                value=event.value
            )
            current_actions.append(action)

            # Heuristic: Create a new step if it's a navigation or a major interaction
            if event.event_type in ["navigate", "submit"]:
                steps.append(AriadneStep(
                    step_index=step_counter,
                    name=f"step_{step_counter}",
                    description=f"Inferred step from {event.event_type}",
                    observe=AriadneObserve(), # TODO: Infer observation from screenshots/DOM
                    actions=list(current_actions)
                ))
                current_actions = []
                step_counter += 1

        # Handle remaining actions
        if current_actions:
            steps.append(AriadneStep(
                step_index=step_counter,
                name=f"final_step",
                description="Final recorded actions",
                observe=AriadneObserve(),
                actions=current_actions
            ))

        return steps

    def _map_event_to_intent(self, event: RawTraceEvent) -> Optional[AriadneIntent]:
        """Maps raw event types to semantic AriadneIntents."""
        mapping = {
            "click": AriadneIntent.CLICK,
            "change": AriadneIntent.FILL,
            "navigate": AriadneIntent.NAVIGATE,
            "keydown": AriadneIntent.PRESS_KEY,
            "upload": AriadneIntent.UPLOAD,
        }
        return mapping.get(event.event_type)
