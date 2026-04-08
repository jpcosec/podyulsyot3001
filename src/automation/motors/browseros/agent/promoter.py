"""Promotion helpers from shared BrowserOS candidates to replay-style paths."""

from __future__ import annotations

from src.automation.ariadne.contracts import (
    ReplayAction,
    ReplayObserve,
    ReplayPath,
    ReplayStep,
    ReplayTarget,
)
from src.automation.motors.browseros.promotion_models import (
    BrowserOSActionCandidate,
    BrowserOSStepCandidate,
)


class BrowserOSLevel2Promoter:
    """Promote shared BrowserOS step candidates into a draft replay path."""

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
        candidates: list[BrowserOSStepCandidate],
    ) -> ReplayPath | None:
        if not candidates:
            return None
        if any(candidate.requires_review for candidate in candidates):
            return None

        steps: list[ReplayStep] = []
        for index, candidate in enumerate(candidates, start=1):
            actions: list[ReplayAction] = []
            for action_candidate in candidate.actions:
                replay_action = self._action_from_candidate(action_candidate)
                if replay_action is None:
                    return None
                actions.append(replay_action)
            if not actions:
                return None
            observe_targets = [
                action.target
                for action in actions
                if action.intent != "navigate" and action.target is not None
            ]
            steps.append(
                ReplayStep(
                    step_index=index,
                    name=f"{self._step_name(candidate)}_{index}",
                    description=self._description(candidate),
                    observe=ReplayObserve(required_elements=observe_targets),
                    actions=actions,
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
        candidate: BrowserOSActionCandidate,
    ) -> ReplayAction | None:
        if candidate.candidate_intent not in self._INTENT_MAP:
            return None
        intent = self._INTENT_MAP[candidate.candidate_intent]
        target = self._target_from_hint(candidate.target_hint)
        if candidate.candidate_intent in self._TARGET_REQUIRED and target is None:
            return None
        if intent == "navigate":
            return ReplayAction(intent=intent, value=candidate.target_hint)
        return ReplayAction(intent=intent, target=target, value=candidate.value_hint)

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

    def _description(self, candidate: BrowserOSStepCandidate) -> str:
        parts: list[str] = []
        for action in candidate.actions:
            part = action.candidate_intent or action.origin
            if action.target_hint:
                part += f" target={action.target_hint}"
            if action.value_hint:
                part += f" value={action.value_hint}"
            parts.append(part)
        return "BrowserOS candidate: " + ", ".join(parts)

    def _step_name(self, candidate: BrowserOSStepCandidate) -> str:
        if not candidate.actions:
            return "review"
        if len(candidate.actions) == 1:
            return candidate.actions[0].candidate_intent or candidate.actions[0].origin
        return "composed"
