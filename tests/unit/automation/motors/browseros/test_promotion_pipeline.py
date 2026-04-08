"""Tests for shared BrowserOS grouping and validation."""

from __future__ import annotations

from src.automation.motors.browseros.promotion_models import (
    BrowserOSActionCandidate,
    BrowserOSStepCandidate,
)
from src.automation.motors.browseros.promotion_pipeline import (
    BrowserOSCandidateGrouper,
    BrowserOSPathValidator,
)


def test_grouper_composes_form_actions_followed_by_submit_click():
    candidates = [
        BrowserOSStepCandidate(
            step_index=1,
            source="level2",
            actions=[
                BrowserOSActionCandidate(
                    source="level2",
                    origin="fill",
                    candidate_intent="fill",
                    target_hint="#first",
                    value_hint="Ada",
                )
            ],
        ),
        BrowserOSStepCandidate(
            step_index=2,
            source="level2",
            actions=[
                BrowserOSActionCandidate(
                    source="level2",
                    origin="fill",
                    candidate_intent="fill",
                    target_hint="#last",
                    value_hint="Lovelace",
                )
            ],
        ),
        BrowserOSStepCandidate(
            step_index=3,
            source="level2",
            actions=[
                BrowserOSActionCandidate(
                    source="level2",
                    origin="click",
                    candidate_intent="click",
                    target_hint="Submit",
                )
            ],
        ),
    ]

    grouped = BrowserOSCandidateGrouper().group(candidates)

    assert len(grouped) == 1
    assert len(grouped[0].actions) == 3


def test_validator_blocks_missing_required_target():
    candidates = [
        BrowserOSStepCandidate(
            step_index=1,
            source="level1",
            actions=[
                BrowserOSActionCandidate(
                    source="level1",
                    origin="fill",
                    candidate_intent="fill",
                    value_hint="Ada",
                )
            ],
        )
    ]

    assessment = BrowserOSPathValidator().assess(candidates)

    assert assessment.outcome in {"blocked", "partial"}
    assert any("missing target" in reason for reason in assessment.reasons)
