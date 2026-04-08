"""Tests for BrowserOS Level 2 candidate promotion."""

from __future__ import annotations

from src.automation.motors.browseros.agent.normalizer import (
    BrowserOSLevel2StepCandidate,
)
from src.automation.motors.browseros.agent.promoter import BrowserOSLevel2Promoter


def test_promote_supported_candidates_to_ariadne_path():
    candidates = [
        BrowserOSLevel2StepCandidate(
            step_index=1,
            tool_name="navigate_page",
            candidate_intent="navigate",
            target_hint="https://example.com/apply",
        ),
        BrowserOSLevel2StepCandidate(
            step_index=2,
            tool_name="fill",
            candidate_intent="fill",
            target_hint="#first-name",
            value_hint="Ada",
        ),
        BrowserOSLevel2StepCandidate(
            step_index=3,
            tool_name="click",
            candidate_intent="click",
            target_hint="Submit application",
        ),
    ]

    path = BrowserOSLevel2Promoter().promote(portal="xing", candidates=candidates)

    assert path is not None
    assert path.task_id == "browseros_level2_discovery"
    assert path.steps[0].actions[0].intent == "navigate"
    assert path.steps[0].actions[0].value == "https://example.com/apply"
    assert path.steps[1].actions[0].intent == "fill"
    assert path.steps[1].actions[0].target.css == "#first-name"
    assert path.steps[2].actions[0].target.text == "Submit application"


def test_promote_returns_none_for_review_required_candidates():
    candidates = [
        BrowserOSLevel2StepCandidate(
            step_index=1,
            tool_name="click",
            candidate_intent="click",
            requires_review=True,
            review_reason="snapshot-local element id",
        )
    ]

    path = BrowserOSLevel2Promoter().promote(portal="xing", candidates=candidates)

    assert path is None


def test_promote_returns_none_when_target_required_but_missing():
    candidates = [
        BrowserOSLevel2StepCandidate(
            step_index=1,
            tool_name="fill",
            candidate_intent="fill",
            value_hint="Ada",
        )
    ]

    path = BrowserOSLevel2Promoter().promote(portal="xing", candidates=candidates)

    assert path is None
