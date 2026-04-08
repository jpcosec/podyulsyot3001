"""Promotion helpers from BrowserOS Level 2 candidates to replay-style paths."""

from __future__ import annotations

from src.automation.ariadne.contracts import (
    ReplayAction,
    ReplayObserve,
    ReplayPath,
    ReplayStep,
    ReplayTarget,
)

from .normalizer import BrowserOSLevel2StepCandidate


class BrowserOSLevel2Promoter:
    """Promote deterministic Level 2 candidates into a draft Ariadne path."""

    _INTENT_MAP = {
        "navigate": "navigate",
        "click": "click",
        "fill": "fill",
        "select": "select",
        "upload": "upload",
        "press_key": "press_key",
        "scroll": "scroll",
    }
    _TARGET_REQUIRED = {"click", "fill", "select", "upload"}

    def promote(
        self,
        *,
        portal: str,
        candidates: list[BrowserOSLevel2StepCandidate],
    ) -> ReplayPath | None:
        if not candidates:
            return None
        if any(candidate.requires_review for candidate in candidates):
            return None

        steps: list[AriadneStep] = []
        for index, candidate in enumerate(candidates, start=1):
            action = self._action_from_candidate(candidate)
            if action is None:
                return None
            target = action.target if action.intent != "navigate" else None
            observe = ReplayObserve(required_elements=[target] if target else [])
            steps.append(
                ReplayStep(
                    step_index=index,
                    name=f"{candidate.candidate_intent or 'review'}_{index}",
                    description=self._description(candidate),
                    observe=observe,
                    actions=[action],
                    human_required=False,
                )
            )

        return ReplayPath(
            id=f"browseros_draft_{portal}",
            task_id="browseros_level2_discovery",
            steps=steps,
        )

    def _action_from_candidate(
        self,
        candidate: BrowserOSLevel2StepCandidate,
    ) -> ReplayAction | None:
        if candidate.candidate_intent not in self._INTENT_MAP:
            return None
        intent = self._INTENT_MAP[candidate.candidate_intent]
        target = self._target_from_hint(candidate.target_hint)
        if candidate.candidate_intent in self._TARGET_REQUIRED and target is None:
            return None
        value = candidate.value_hint
        if intent == "navigate":
            return ReplayAction(intent=intent, value=candidate.target_hint)
        return ReplayAction(intent=intent, target=target, value=value)

    def _target_from_hint(self, hint: str | None) -> ReplayTarget | None:
        if not hint:
            return None
        if self._looks_like_selector(hint):
            return ReplayTarget(css=hint)
        return ReplayTarget(text=hint)

    def _looks_like_selector(self, value: str) -> bool:
        return value.startswith(
            ("#", ".", "[", "input", "button", "select", "textarea")
        )

    def _description(self, candidate: BrowserOSLevel2StepCandidate) -> str:
        parts = [candidate.candidate_intent or candidate.tool_name]
        if candidate.target_hint:
            parts.append(f"target={candidate.target_hint}")
        if candidate.value_hint:
            parts.append(f"value={candidate.value_hint}")
        return "BrowserOS Level 2 candidate: " + ", ".join(parts)
