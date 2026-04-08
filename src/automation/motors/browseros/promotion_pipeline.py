"""Shared BrowserOS grouping and validation pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.automation.motors.browseros.promotion_models import (
    BrowserOSActionCandidate,
    BrowserOSStepCandidate,
)


class BrowserOSPathAssessment(BaseModel):
    """Validation outcome for promoted BrowserOS candidates."""

    outcome: Literal["promotable", "partial", "blocked"]
    reasons: list[str] = Field(default_factory=list)


class BrowserOSCandidateGrouper:
    """Compose single-action candidates into more realistic replay steps."""

    _FORM_ACTIONS = {"fill", "select", "upload", "press_key", "scroll"}

    def group(
        self, candidates: list[BrowserOSStepCandidate]
    ) -> list[BrowserOSStepCandidate]:
        grouped: list[BrowserOSStepCandidate] = []
        current: BrowserOSStepCandidate | None = None
        step_index = 1
        for candidate in candidates:
            if candidate.requires_review or not candidate.actions:
                if current is not None:
                    grouped.append(current)
                    current = None
                    step_index += 1
                grouped.append(candidate.model_copy(update={"step_index": step_index}))
                step_index += 1
                continue

            action = candidate.actions[0]
            intent = action.candidate_intent
            if intent == "navigate":
                if current is not None:
                    grouped.append(current)
                    current = None
                    step_index += 1
                grouped.append(candidate.model_copy(update={"step_index": step_index}))
                step_index += 1
                continue

            if current is None:
                current = candidate.model_copy(update={"step_index": step_index})
                if intent == "click":
                    grouped.append(current)
                    current = None
                    step_index += 1
                continue

            previous_intents = {a.candidate_intent for a in current.actions}
            if intent in self._FORM_ACTIONS and previous_intents <= self._FORM_ACTIONS:
                current.actions.extend(candidate.actions)
                continue

            if intent == "click" and previous_intents <= self._FORM_ACTIONS:
                current.actions.extend(candidate.actions)
                grouped.append(current)
                current = None
                step_index += 1
                continue

            grouped.append(current)
            step_index += 1
            current = candidate.model_copy(update={"step_index": step_index})
            if intent == "click":
                grouped.append(current)
                current = None
                step_index += 1

        if current is not None:
            grouped.append(current)
        return grouped


class BrowserOSPathValidator:
    """Assess whether BrowserOS candidates are safe enough to promote."""

    _TARGET_REQUIRED = {"click", "fill", "select", "upload"}

    def assess(
        self, candidates: list[BrowserOSStepCandidate]
    ) -> BrowserOSPathAssessment:
        reasons: list[str] = []
        has_partial = False
        if not candidates:
            return BrowserOSPathAssessment(
                outcome="blocked", reasons=["no candidates available"]
            )
        for step in candidates:
            if step.requires_review:
                reasons.append(
                    step.review_reason or f"step {step.step_index} requires review"
                )
                continue
            for action in step.actions:
                if action.requires_review:
                    reasons.append(
                        action.review_reason
                        or f"action in step {step.step_index} requires review"
                    )
                if (
                    action.candidate_intent in self._TARGET_REQUIRED
                    and not action.target_hint
                ):
                    reasons.append(
                        f"missing target for {action.candidate_intent} in step {step.step_index}"
                    )
                if action.candidate_intent == "navigate" and not action.target_hint:
                    reasons.append(f"missing navigation URL in step {step.step_index}")
                if (
                    action.candidate_intent in {"fill", "select"}
                    and action.value_hint is None
                ):
                    has_partial = True
                    reasons.append(
                        f"missing value for {action.candidate_intent} in step {step.step_index}"
                    )
        if reasons:
            return BrowserOSPathAssessment(
                outcome="blocked" if not has_partial else "partial", reasons=reasons
            )
        return BrowserOSPathAssessment(outcome="promotable")
