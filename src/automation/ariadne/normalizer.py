"""Ariadne trace normalization into stable draft portal maps.

This module groups raw trace events into semantic steps, infers reusable portal
states, and synthesizes observation predicates that are suitable for deterministic
replay and later promotion.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

from .models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadnePath,
    AriadnePortalMap,
    AriadneState,
    AriadneStep,
    AriadneTarget,
    AriadneTask,
)
from .trace_models import AriadneSessionTrace, RawTraceEvent

logger = logging.getLogger(__name__)

_STEP_GAP_SECONDS = 3.0
_TEXT_KEYS = ("text", "label", "aria_label", "placeholder", "name")


class AriadneNormalizer:
    """Heuristic-based normalizer for converting traces to maps."""

    def normalize(self, trace: AriadneSessionTrace) -> AriadnePortalMap:
        """Convert a raw recording session into a draft Ariadne portal map."""
        logger.info("Normalizing trace for portal: %s", trace.portal_name)
        groups = self._group_events(trace.events)
        state_targets = self._collect_state_targets(groups)
        states = self._build_states(groups, state_targets)
        steps = self._build_steps(groups, state_targets)
        tasks = self._build_tasks(steps, trace.portal_name)
        path = AriadnePath(id="recorded_flow", task_id="inferred_task", steps=steps)
        return AriadnePortalMap(
            portal_name=trace.portal_name,
            base_url=self._resolve_base_url(trace.events),
            states=states,
            tasks=tasks,
            paths={"recorded_flow": path},
        )

    def _group_events(self, events: list[RawTraceEvent]) -> list[list[RawTraceEvent]]:
        groups: list[list[RawTraceEvent]] = []
        current: list[RawTraceEvent] = []
        current_signature: Optional[str] = None
        previous_action_time = None

        for event in events:
            intent = self._map_event_to_intent(event)
            signature = self._state_signature(event)
            should_split = False

            if current:
                if event.event_type == "navigate":
                    should_split = True
                elif current_signature and signature and signature != current_signature:
                    should_split = True
                elif (
                    intent is not None
                    and previous_action_time is not None
                    and (event.timestamp - previous_action_time).total_seconds()
                    > _STEP_GAP_SECONDS
                ):
                    should_split = True

            if should_split:
                groups.append(current)
                current = []
                current_signature = None
                previous_action_time = None

            current.append(event)
            current_signature = current_signature or signature
            if intent is not None:
                previous_action_time = event.timestamp

            if event.event_type == "navigate":
                groups.append(current)
                current = []
                current_signature = None
                previous_action_time = None

        if current:
            groups.append(current)
        return [
            group
            for group in groups
            if any(self._map_event_to_intent(event) for event in group)
        ]

    def _collect_state_targets(
        self, groups: list[list[RawTraceEvent]]
    ) -> dict[str, list[AriadneTarget]]:
        action_targets: dict[
            str, dict[tuple[Optional[str], Optional[str]], AriadneTarget]
        ] = defaultdict(dict)
        evidence_counts: dict[str, dict[tuple[Optional[str], Optional[str]], int]] = (
            defaultdict(lambda: defaultdict(int))
        )

        for group in groups:
            state_id = self._infer_state_id(group)
            for event in group:
                target = self._target_from_event(event)
                if target is not None and event.event_type != "navigate":
                    action_targets[state_id][self._target_key(target)] = target
                for evidence in self._evidence_targets(event):
                    evidence_counts[state_id][self._target_key(evidence)] += 1

        state_targets: dict[str, list[AriadneTarget]] = {}
        for state_id in {self._infer_state_id(group) for group in groups}:
            required = dict(action_targets[state_id])
            for key, count in evidence_counts[state_id].items():
                if count >= 2 and key not in required:
                    required[key] = AriadneTarget(css=key[0], text=key[1])
            state_targets[state_id] = self._sort_targets(required.values())
        return state_targets

    def _build_states(
        self,
        groups: list[list[RawTraceEvent]],
        state_targets: dict[str, list[AriadneTarget]],
    ) -> dict[str, AriadneState]:
        labels: dict[str, str] = {}
        for group in groups:
            state_id = self._infer_state_id(group)
            labels.setdefault(state_id, self._state_label(group))

        return {
            state_id: AriadneState(
                id=state_id,
                description=labels[state_id],
                presence_predicate=AriadneObserve(required_elements=targets),
            )
            for state_id, targets in state_targets.items()
        }

    def _build_steps(
        self,
        groups: list[list[RawTraceEvent]],
        state_targets: dict[str, list[AriadneTarget]],
    ) -> list[AriadneStep]:
        steps: list[AriadneStep] = []
        for index, group in enumerate(groups, start=1):
            state_id = self._infer_state_id(group)
            label = self._state_label(group)
            actions = [
                action
                for event in group
                if (action := self._action_from_event(event)) is not None
            ]
            primary_intent = actions[0].intent.value if actions else "observe"
            steps.append(
                AriadneStep(
                    step_index=index,
                    name=f"{primary_intent}_{state_id}",
                    description=f"{primary_intent.replace('_', ' ').title()} on {label}",
                    state_id=state_id,
                    observe=AriadneObserve(required_elements=state_targets[state_id]),
                    actions=actions,
                )
            )
        return steps

    def _build_tasks(
        self, steps: list[AriadneStep], portal_name: str
    ) -> dict[str, AriadneTask]:
        entry_state = steps[0].state_id or "unknown_state"
        success_state = steps[-1].state_id or entry_state
        return {
            "inferred_task": AriadneTask(
                id="inferred_task",
                goal=f"Complete recorded flow for {portal_name}",
                entry_state=entry_state,
                success_states=[success_state],
                failure_states=[],
            )
        }

    def _action_from_event(self, event: RawTraceEvent) -> Optional[AriadneAction]:
        intent = self._map_event_to_intent(event)
        if intent is None:
            return None
        value = event.value
        if intent == AriadneIntent.NAVIGATE:
            value = event.url or event.page_url or event.value
        return AriadneAction(
            intent=intent, target=self._target_from_event(event), value=value
        )

    def _target_from_event(self, event: RawTraceEvent) -> Optional[AriadneTarget]:
        css = event.selector or self._first_selector(event.selectors)
        text = self._extract_text(event)
        if event.event_type == "navigate":
            css = None
            text = (
                text
                or event.page_title
                or self._title_from_url(event.url or event.page_url)
            )
        region = self._extract_region(event.metadata)
        if css is None and text is None and region is None:
            return None
        return AriadneTarget(css=css, text=text, region=region)

    def _evidence_targets(self, event: RawTraceEvent) -> list[AriadneTarget]:
        evidence: dict[tuple[Optional[str], Optional[str]], AriadneTarget] = {}
        target = self._target_from_event(event)
        if target is not None and event.event_type != "navigate":
            evidence[self._target_key(target)] = target

        for item in event.metadata.get("visible_selectors", []):
            if isinstance(item, dict):
                candidate = AriadneTarget(css=item.get("css"), text=item.get("text"))
                if candidate.css or candidate.text:
                    evidence[self._target_key(candidate)] = candidate
        return self._sort_targets(evidence.values())

    def _infer_state_id(self, group: list[RawTraceEvent]) -> str:
        signature = self._state_signature(group[0]) or "recorded_state"
        cleaned = re.sub(r"[^a-z0-9]+", "_", signature.lower()).strip("_")
        return cleaned or "recorded_state"

    def _state_label(self, group: list[RawTraceEvent]) -> str:
        event = group[0]
        if event.page_title:
            return event.page_title.strip()
        if event.screenshot_path:
            return (
                Path(event.screenshot_path)
                .stem.replace("-", " ")
                .replace("_", " ")
                .title()
            )
        return self._title_from_url(event.page_url or event.url) or "Recorded State"

    def _state_signature(self, event: RawTraceEvent) -> Optional[str]:
        if event.screenshot_path:
            return Path(event.screenshot_path).stem
        if event.page_title:
            return event.page_title
        return self._path_signature(event.page_url or event.url)

    def _resolve_base_url(self, events: list[RawTraceEvent]) -> str:
        for event in events:
            if event.page_url:
                return event.page_url
            if event.url:
                return event.url
        return ""

    def _extract_text(self, event: RawTraceEvent) -> Optional[str]:
        for key in _TEXT_KEYS:
            value = event.metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_region(self, metadata: dict) -> Optional[dict[str, int]]:
        if not isinstance(metadata, dict):
            return None
        region = metadata.get("region")
        if isinstance(region, dict):
            return region
        keys = ("x", "y", "w", "h")
        if all(isinstance(metadata.get(key), int) for key in keys):
            return {key: metadata[key] for key in keys}
        return None

    def _first_selector(self, selectors: Optional[list[list[str]]]) -> Optional[str]:
        if not selectors:
            return None
        for selector_group in selectors:
            if selector_group:
                return selector_group[0]
        return None

    def _path_signature(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        path = urlparse(url).path.strip("/")
        return path or urlparse(url).netloc or None

    def _title_from_url(self, url: Optional[str]) -> Optional[str]:
        signature = self._path_signature(url)
        if not signature:
            return None
        return signature.split("/")[-1].replace("-", " ").replace("_", " ").title()

    def _sort_targets(self, targets: Iterable[AriadneTarget]) -> list[AriadneTarget]:
        return sorted(
            targets, key=lambda target: ((target.css or "~"), target.text or "")
        )

    def _target_key(self, target: AriadneTarget) -> tuple[Optional[str], Optional[str]]:
        return (target.css, target.text)

    def _map_event_to_intent(self, event: RawTraceEvent) -> Optional[AriadneIntent]:
        mapping = {
            "click": AriadneIntent.CLICK,
            "change": AriadneIntent.FILL,
            "keydown": AriadneIntent.PRESS_KEY,
            "navigate": AriadneIntent.NAVIGATE,
            "scroll": AriadneIntent.SCROLL,
            "select": AriadneIntent.SELECT,
            "submit": AriadneIntent.CLICK,
            "upload": AriadneIntent.UPLOAD,
            "wait": AriadneIntent.WAIT,
        }
        return mapping.get(event.event_type)
