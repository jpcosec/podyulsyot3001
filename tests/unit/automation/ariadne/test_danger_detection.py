"""Unit tests for apply-time danger detection."""

from __future__ import annotations

from src.automation.ariadne.danger_contracts import ApplyDangerSignals
from src.automation.ariadne.danger_detection import ApplyDangerDetector


def test_detector_flags_prior_submission_as_duplicate_abort():
    detector = ApplyDangerDetector()

    report = detector.detect(ApplyDangerSignals(already_submitted=True))

    assert report.primary is not None
    assert report.primary.code == "duplicate_submission"
    assert report.primary.recommended_action == "abort"


def test_detector_flags_captcha_from_dom_text():
    detector = ApplyDangerDetector()

    report = detector.detect(
        ApplyDangerSignals(dom_text="Complete the CAPTCHA security check to continue")
    )

    assert report.primary is not None
    assert report.primary.code == "captcha_challenge"
    assert report.primary.source == "dom_text"


def test_detector_flags_offsite_redirect_from_live_url():
    detector = ApplyDangerDetector()

    report = detector.detect(
        ApplyDangerSignals(
            current_url="https://jobs.greenhouse.io/acme/apply",
            application_url="https://www.xing.com/jobs/apply/123",
            route_outcome="onsite",
        )
    )

    assert report.primary is not None
    assert report.primary.code == "external_application_route"
    assert report.primary.source == "routing"


def test_detector_uses_screenshot_text_when_dom_is_unavailable():
    detector = ApplyDangerDetector()

    report = detector.detect(
        ApplyDangerSignals(screenshot_text="You have already applied to this role")
    )

    assert report.primary is not None
    assert report.primary.code == "duplicate_submission"
    assert report.primary.source == "screenshot"


def test_detector_flags_email_route_as_pause():
    detector = ApplyDangerDetector()

    report = detector.detect(
        ApplyDangerSignals(
            route_outcome="email",
            route_reason="Enriched ingest state requires an email application handoff.",
        )
    )

    assert report.primary is not None
    assert report.primary.code == "email_application_route"
    assert report.primary.recommended_action == "abort"


def test_detector_flags_unsupported_route_as_external():
    detector = ApplyDangerDetector()

    report = detector.detect(
        ApplyDangerSignals(
            route_outcome="unsupported",
            route_reason="No usable route found.",
        )
    )

    assert report.primary is not None
    assert report.primary.code == "unsupported_application_route"
