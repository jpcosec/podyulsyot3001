"""Tests for Ariadne trace normalization."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.automation.ariadne.normalizer import AriadneNormalizer
from src.automation.ariadne.trace_models import AriadneSessionTrace, RawTraceEvent


def test_normalize_builds_canonical_states_and_observations() -> None:
    start = datetime(2026, 4, 7, 10, 0, 0)
    trace = AriadneSessionTrace(
        session_id="session-1",
        portal_name="example_portal",
        start_time=start,
        events=[
            RawTraceEvent(
                timestamp=start,
                event_type="navigate",
                url="https://example.com/apply",
                page_title="Application Form",
                page_url="https://example.com/apply",
                screenshot_path="screenshots/application-form.png",
                metadata={
                    "visible_selectors": [
                        {"css": "form.application-form", "text": "Application form"},
                        {"css": "button.continue", "text": "Continue"},
                    ]
                },
            ),
            RawTraceEvent(
                timestamp=start + timedelta(seconds=1),
                event_type="change",
                selector="#first_name",
                value="{{profile.first_name}}",
                page_title="Application Form",
                page_url="https://example.com/apply",
                screenshot_path="screenshots/application-form.png",
                metadata={"label": "First name"},
            ),
            RawTraceEvent(
                timestamp=start + timedelta(seconds=2),
                event_type="change",
                selector="#email",
                value="{{profile.email}}",
                page_title="Application Form",
                page_url="https://example.com/apply",
                screenshot_path="screenshots/application-form.png",
                metadata={"label": "Email"},
            ),
            RawTraceEvent(
                timestamp=start + timedelta(seconds=3),
                event_type="click",
                selector="button.continue",
                page_title="Application Form",
                page_url="https://example.com/apply",
                screenshot_path="screenshots/application-form.png",
                metadata={"text": "Continue"},
            ),
            RawTraceEvent(
                timestamp=start + timedelta(seconds=4),
                event_type="navigate",
                url="https://example.com/apply/review",
                page_title="Review Page",
                page_url="https://example.com/apply/review",
                screenshot_path="screenshots/review-page.png",
                metadata={
                    "visible_selectors": [
                        {
                            "css": "div.review-summary",
                            "text": "Review your application",
                        },
                        {"css": "button.submit", "text": "Submit application"},
                    ]
                },
            ),
            RawTraceEvent(
                timestamp=start + timedelta(seconds=5),
                event_type="submit",
                selector="button.submit",
                page_title="Review Page",
                page_url="https://example.com/apply/review",
                screenshot_path="screenshots/review-page.png",
                metadata={"text": "Submit application"},
            ),
        ],
    )

    portal_map = AriadneNormalizer().normalize(trace)

    assert portal_map.model_dump(exclude_none=True) == {
        "portal_name": "example_portal",
        "base_url": "https://example.com/apply",
        "states": {
            "application_form": {
                "id": "application_form",
                "description": "Application Form",
                "presence_predicate": {
                    "required_elements": [
                        {"css": "#email", "text": "Email"},
                        {"css": "#first_name", "text": "First name"},
                        {"css": "button.continue", "text": "Continue"},
                    ],
                    "forbidden_elements": [],
                    "logical_op": "AND",
                },
                "components": {},
                "transitions": {},
            },
            "review_page": {
                "id": "review_page",
                "description": "Review Page",
                "presence_predicate": {
                    "required_elements": [
                        {"css": "button.submit", "text": "Submit application"},
                    ],
                    "forbidden_elements": [],
                    "logical_op": "AND",
                },
                "components": {},
                "transitions": {},
            },
        },
        "tasks": {
            "inferred_task": {
                "id": "inferred_task",
                "goal": "Complete recorded flow for example_portal",
                "entry_state": "application_form",
                "success_states": ["review_page"],
                "failure_states": [],
                "success_criteria": {},
                "blocker_recovery": [],
            }
        },
        "paths": {
            "recorded_flow": {
                "id": "recorded_flow",
                "task_id": "inferred_task",
                "steps": [
                    {
                        "step_index": 1,
                        "name": "navigate_application_form",
                        "description": "Navigate on Application Form",
                        "state_id": "application_form",
                        "observe": {
                            "required_elements": [
                                {"css": "#email", "text": "Email"},
                                {"css": "#first_name", "text": "First name"},
                                {"css": "button.continue", "text": "Continue"},
                            ],
                            "forbidden_elements": [],
                            "logical_op": "AND",
                        },
                        "actions": [
                            {
                                "intent": "navigate",
                                "target": {"text": "Application Form"},
                                "value": "https://example.com/apply",
                                "optional": False,
                                "metadata": {},
                            }
                        ],
                        "human_required": False,
                        "dry_run_stop": False,
                        "metadata": {},
                    },
                    {
                        "step_index": 2,
                        "name": "fill_application_form",
                        "description": "Fill on Application Form",
                        "state_id": "application_form",
                        "observe": {
                            "required_elements": [
                                {"css": "#email", "text": "Email"},
                                {"css": "#first_name", "text": "First name"},
                                {"css": "button.continue", "text": "Continue"},
                            ],
                            "forbidden_elements": [],
                            "logical_op": "AND",
                        },
                        "actions": [
                            {
                                "intent": "fill",
                                "target": {"css": "#first_name", "text": "First name"},
                                "value": "{{profile.first_name}}",
                                "optional": False,
                                "metadata": {},
                            },
                            {
                                "intent": "fill",
                                "target": {"css": "#email", "text": "Email"},
                                "value": "{{profile.email}}",
                                "optional": False,
                                "metadata": {},
                            },
                            {
                                "intent": "click",
                                "target": {
                                    "css": "button.continue",
                                    "text": "Continue",
                                },
                                "optional": False,
                                "metadata": {},
                            },
                        ],
                        "human_required": False,
                        "dry_run_stop": False,
                        "metadata": {},
                    },
                    {
                        "step_index": 3,
                        "name": "navigate_review_page",
                        "description": "Navigate on Review Page",
                        "state_id": "review_page",
                        "observe": {
                            "required_elements": [
                                {"css": "button.submit", "text": "Submit application"},
                            ],
                            "forbidden_elements": [],
                            "logical_op": "AND",
                        },
                        "actions": [
                            {
                                "intent": "navigate",
                                "target": {"text": "Review Page"},
                                "value": "https://example.com/apply/review",
                                "optional": False,
                                "metadata": {},
                            }
                        ],
                        "human_required": False,
                        "dry_run_stop": False,
                        "metadata": {},
                    },
                    {
                        "step_index": 4,
                        "name": "click_review_page",
                        "description": "Click on Review Page",
                        "state_id": "review_page",
                        "observe": {
                            "required_elements": [
                                {"css": "button.submit", "text": "Submit application"},
                            ],
                            "forbidden_elements": [],
                            "logical_op": "AND",
                        },
                        "actions": [
                            {
                                "intent": "click",
                                "target": {
                                    "css": "button.submit",
                                    "text": "Submit application",
                                },
                                "optional": False,
                                "metadata": {},
                            }
                        ],
                        "human_required": False,
                        "dry_run_stop": False,
                        "metadata": {},
                    },
                ],
                "metadata": {},
            }
        },
        "global_components": {},
    }


def test_normalize_uses_selector_fallbacks_instead_of_page_title_placeholders() -> None:
    event = RawTraceEvent(
        timestamp=datetime(2026, 4, 7, 10, 0, 0),
        event_type="change",
        selectors=[["#phone"], ["input[name='phone']"]],
        value="123",
        page_title="Candidate Profile",
        page_url="https://example.com/profile",
        metadata={"name": "Phone number"},
    )

    portal_map = AriadneNormalizer().normalize(
        AriadneSessionTrace(
            session_id="session-2",
            portal_name="example_portal",
            start_time=event.timestamp,
            events=[event],
        )
    )

    action = portal_map.paths["recorded_flow"].steps[0].actions[0]

    assert action.target is not None
    assert action.target.css == "#phone"
    assert action.target.text == "Phone number"
    assert action.target.text != "Candidate Profile"
