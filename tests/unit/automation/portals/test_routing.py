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


# ─── Comprehensive routing matrix covering all four outcomes ──────────────────


def test_xing_routing_onsite_with_normalized_payload() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "job_title": "Senior Data Engineer",
            "company_name": "TechCorp GmbH",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Build pipelines"],
            "requirements": ["Python"],
            "application_method": "onsite",
            "application_url": "https://www.xing.com/jobs/senior-data-engineer-456/apply",
            "url": "https://www.xing.com/jobs/senior-data-engineer-456",
        },
    )
    assert route.outcome == "onsite"
    assert route.path_id == "standard_easy_apply"


def test_xing_routing_external_url_when_ats_is_different_host() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "application_method": "direct_url",
            "application_url": "https://apply.workable.com/acme/jobs/789",
            "url": "https://www.xing.com/jobs/data-engineer-789",
        },
    )
    assert route.outcome == "external_url"
    assert route.application_url == "https://apply.workable.com/acme/jobs/789"
    assert route.path_id is None


def test_xing_routing_email_handoff_from_method() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "application_method": "email",
            "application_email": "karriere@example.com",
            "url": "https://www.xing.com/jobs/backend-engineer-321",
        },
    )
    assert route.outcome == "email"
    assert route.application_email == "karriere@example.com"


def test_xing_routing_unsupported_when_no_url_or_email() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "job_title": "Data Engineer",
            "company_name": "TechCorp",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Build pipelines"],
            "requirements": ["Python"],
        },
    )
    assert route.outcome == "unsupported"
    assert "not provide" in route.reason.lower()


def test_xing_routing_email_falls_back_when_only_email_provided() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "application_email": "jobs@example.com",
            "url": "https://www.xing.com/jobs/software-engineer-999",
        },
    )
    assert route.outcome == "email"
    assert route.application_email == "jobs@example.com"


def test_stepstone_routing_onsite_when_apply_stays_on_stepstone() -> None:
    route = resolve_portal_routing(
        "stepstone",
        {
            "application_method": "onsite",
            "application_url": "https://www.stepstone.de/bewerben/abc123",
            "url": "https://www.stepstone.de/stellenangebote--data-engineer-abc123",
        },
    )
    assert route.outcome == "onsite"
    assert route.path_id == "standard_easy_apply"


def test_stepstone_routing_external_url_when_ats_is_different_host() -> None:
    route = resolve_portal_routing(
        "stepstone",
        {
            "application_method": "direct_url",
            "application_url": "https://jobs.lever.co/techco/456",
            "url": "https://www.stepstone.de/stellenangebote--data-engineer-456",
        },
    )
    assert route.outcome == "external_url"


def test_stepstone_routing_unsupported_when_no_url_or_email() -> None:
    route = resolve_portal_routing(
        "stepstone",
        {
            "job_title": "Data Engineer",
            "company_name": "TechCo",
            "location": "Munich",
            "employment_type": "Full-time",
            "responsibilities": ["Build pipelines"],
            "requirements": ["Python"],
        },
    )
    assert route.outcome == "unsupported"


def test_linkedin_routing_onsite_when_apply_stays_on_linkedin() -> None:
    route = resolve_portal_routing(
        "linkedin",
        {
            "application_method": "onsite",
            "application_url": "https://www.linkedin.com/jobs/apply/789",
            "url": "https://www.linkedin.com/jobs/software-engineer-789",
        },
    )
    assert route.outcome == "onsite"
    assert route.path_id == "standard_easy_apply"


def test_linkedin_routing_email_when_only_email_provided() -> None:
    route = resolve_portal_routing(
        "linkedin",
        {
            "application_email": "recruiting@techcorp.com",
            "url": "https://www.linkedin.com/jobs/software-engineer-123",
        },
    )
    assert route.outcome == "email"


def test_linkedin_routing_unsupported_when_no_url_or_email() -> None:
    route = resolve_portal_routing(
        "linkedin",
        {
            "job_title": "Software Engineer",
            "company_name": "TechCo",
            "location": "Berlin",
            "employment_type": "Full-time",
            "responsibilities": ["Code"],
            "requirements": ["Python"],
        },
    )
    assert route.outcome == "unsupported"


def test_stepstone_routing_normalizes_apply_by_email_method() -> None:
    route = resolve_portal_routing(
        "stepstone",
        {
            "application_method": "Apply by email",
            "application_email": "mailto:hr@stepstone-test.de",
            "url": "https://www.stepstone.de/stellenangebote--engineer-xyz",
        },
    )
    assert route.outcome == "email"
    assert route.application_email == "hr@stepstone-test.de"


def test_routing_strips_mailto_prefix_from_email() -> None:
    route = resolve_portal_routing(
        "stepstone",
        {
            "application_email": "mailto:jobs@example.com?subject=Application",
            "url": "https://www.stepstone.de/stellenangebote--engineer-abc",
        },
    )
    assert route.outcome == "email"
    assert route.application_email == "jobs@example.com"
    assert "?" not in route.application_email


def test_routing_ignores_mailto_in_application_url() -> None:
    route = resolve_portal_routing(
        "xing",
        {
            "application_url": "mailto:jobs@example.com",
            "url": "https://www.xing.com/jobs/engineer-1",
        },
    )
    assert route.outcome == "unsupported"


def test_routing_rejects_invalid_url_schemes() -> None:
    route = resolve_portal_routing(
        "linkedin",
        {
            "application_url": "ftp://files.example.com/resume.pdf",
            "url": "https://www.linkedin.com/jobs/engineer-2",
        },
    )
    assert route.outcome == "unsupported"
