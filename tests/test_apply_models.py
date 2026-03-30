"""Tests for apply module models (spec Section 3)."""
from src.apply.models import ApplicationRecord, ApplyMeta, FormSelectors


def test_form_selectors_mandatory_fields_required():
    """FormSelectors requires all four mandatory selectors."""
    import pytest
    with pytest.raises(Exception):
        FormSelectors()  # missing mandatory fields

    sel = FormSelectors(
        apply_button="button[data-testid='apply']",
        cv_upload="input[type='file']",
        submit_button="button[type='submit']",
        success_indicator=".application-success",
    )
    assert sel.first_name is None
    assert sel.cv_select_existing is None


def test_form_selectors_optional_fields():
    """Optional selectors default to None."""
    sel = FormSelectors(
        apply_button="button",
        cv_upload="input",
        submit_button="button",
        success_indicator=".success",
        first_name="input[name='firstName']",
        cv_select_existing="button.select-cv",
    )
    assert sel.first_name == "input[name='firstName']"
    assert sel.last_name is None


def test_apply_meta_status_values():
    """ApplyMeta accepts only the four defined status values."""
    import pytest
    for status in ("submitted", "dry_run", "failed", "portal_changed"):
        m = ApplyMeta(status=status, timestamp="2026-03-30T00:00:00Z")
        assert m.status == status
    with pytest.raises(Exception):
        ApplyMeta(status="unknown", timestamp="2026-03-30T00:00:00Z")


def test_apply_meta_serialization():
    """ApplyMeta.model_dump() produces a plain dict."""
    m = ApplyMeta(status="submitted", timestamp="2026-03-30T00:00:00Z")
    d = m.model_dump()
    assert d["status"] == "submitted"
    assert d["error"] is None


def test_application_record_round_trip():
    """ApplicationRecord serializes and deserializes cleanly."""
    rec = ApplicationRecord(
        source="xing",
        job_id="12345",
        job_title="Data Engineer",
        company_name="Acme GmbH",
        application_url="https://xing.com/jobs/data-engineer-12345",
        cv_path="/path/to/cv.pdf",
        letter_path=None,
        fields_filled=["first_name", "last_name", "email"],
        dry_run=False,
        submitted_at="2026-03-30T00:00:00Z",
        confirmation_text="Your application was received.",
    )
    d = rec.model_dump()
    assert d["source"] == "xing"
    assert d["letter_path"] is None
    assert d["dry_run"] is False


def test_build_parser_requires_source():
    """build_parser() creates a parser that requires --source."""
    import pytest
    from src.apply.main import build_parser
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_apply_mode():
    """build_parser() parses apply mode args."""
    from src.apply.main import build_parser
    parser = build_parser()
    args = parser.parse_args([
        "--source", "xing",
        "--job-id", "12345",
        "--cv", "/path/cv.pdf",
        "--dry-run",
    ])
    assert args.source == "xing"
    assert args.job_id == "12345"
    assert args.cv_path == "/path/cv.pdf"
    assert args.dry_run is True
    assert args.setup_session is False


def test_build_parser_setup_session_mode():
    """build_parser() parses setup-session mode."""
    from src.apply.main import build_parser
    parser = build_parser()
    args = parser.parse_args(["--source", "xing", "--setup-session"])
    assert args.setup_session is True
    assert args.job_id is None
