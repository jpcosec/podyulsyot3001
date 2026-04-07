"""Regression coverage for portal-specific apply routing modules."""

from __future__ import annotations

from src.automation.portals.routing import resolve_portal_routing


def test_xing_routing_resolves_internal_apply_to_onsite_path() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "application_method": "onsite",
            "application_url": "https://www.xing.com/jobs/software-engineer-123/apply",
            "url": "https://www.xing.com/jobs/software-engineer-123",
        },
    )

    assert route.outcome == "onsite"
    assert route.path_id == "standard_easy_apply"
    assert (
        route.application_url == "https://www.xing.com/jobs/software-engineer-123/apply"
    )


def test_linkedin_routing_resolves_external_ats_redirect() -> None:
    route = resolve_portal_routing(
        "linkedin",
        {
            "application_method": "direct_url",
            "application_url": "https://company.example.test/greenhouse/apply/123",
            "url": "https://www.linkedin.com/jobs/view/123",
        },
    )

    assert route.outcome == "external_url"
    assert route.path_id is None
    assert route.application_url == "https://company.example.test/greenhouse/apply/123"


def test_stepstone_routing_resolves_email_handoff() -> None:
    route = resolve_portal_routing(
        "stepstone",
        {
            "application_method": "Apply by email",
            "application_email": "mailto:jobs@example.test?subject=Apply",
            "url": "https://www.stepstone.de/stellenangebote--data-engineer-123",
        },
    )

    assert route.outcome == "email"
    assert route.application_email == "jobs@example.test"
