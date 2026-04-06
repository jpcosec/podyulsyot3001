# tests/unit/automation/motors/crawl4ai/test_models.py
"""Tests for C4AI motor models."""
from __future__ import annotations

import pytest

from src.automation.motors.crawl4ai.models import (
    ApplicationRecord,
    ApplyMeta,
    JobPosting,
)


def test_job_posting_requires_mandatory_fields():
    with pytest.raises(Exception):
        JobPosting()

    posting = JobPosting(
        job_title="Data Engineer",
        company_name="Acme GmbH",
        location="Berlin",
        employment_type="Full-time",
        responsibilities=["Build pipelines"],
        requirements=["Python"],
    )
    assert posting.job_title == "Data Engineer"
    assert posting.salary is None


def test_apply_meta_status_values():
    for status in ("submitted", "dry_run", "failed", "portal_changed"):
        m = ApplyMeta(status=status, timestamp="2026-03-30T00:00:00Z")
        assert m.status == status

    with pytest.raises(Exception):
        ApplyMeta(status="unknown", timestamp="2026-03-30T00:00:00Z")


def test_apply_meta_serialization():
    m = ApplyMeta(status="submitted", timestamp="2026-03-30T00:00:00Z")
    d = m.model_dump()
    assert d["status"] == "submitted"
    assert d["error"] is None


def test_application_record_round_trip():
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
