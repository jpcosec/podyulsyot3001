"""Tests for Ariadne portal schema models."""
from __future__ import annotations

import pytest

from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
    ScrapePortalDefinition,
)


def test_field_type_values():
    assert FieldType.TEXT == "text"
    assert FieldType.EMAIL == "email"
    assert FieldType.PHONE == "phone"
    assert FieldType.FILE_PDF == "file_pdf"


def test_form_field_required_fields():
    field = FormField(
        name="first_name",
        label="First name",
        required=False,
        field_type=FieldType.TEXT,
    )
    assert field.name == "first_name"
    assert field.required is False


def test_apply_step_defaults():
    step = ApplyStep(name="submit", description="Submit the form", fields=[])
    assert step.dry_run_stop is False


def test_apply_step_dry_run_stop():
    step = ApplyStep(
        name="submit", description="Submit the form", fields=[], dry_run_stop=True
    )
    assert step.dry_run_stop is True


def test_apply_portal_definition_round_trip():
    defn = ApplyPortalDefinition(
        source_name="testportal",
        base_url="https://test.example.com",
        entry_description="Test apply modal",
        steps=[
            ApplyStep(
                name="fill",
                description="Fill form",
                fields=[
                    FormField(
                        name="cv",
                        label="CV",
                        required=True,
                        field_type=FieldType.FILE_PDF,
                    )
                ],
            )
        ],
    )
    assert defn.source_name == "testportal"
    assert defn.steps[0].fields[0].required is True


def test_scrape_portal_definition():
    defn = ScrapePortalDefinition(
        source_name="testportal",
        base_url="https://test.example.com",
        supported_params=["job_query", "city"],
        job_id_pattern=r"-(\d+)$",
    )
    assert "job_query" in defn.supported_params
    assert defn.job_id_pattern == r"-(\d+)$"


def test_scrape_portal_job_id_pattern_is_valid_regex():
    import re

    defn = ScrapePortalDefinition(
        source_name="testportal",
        base_url="https://test.example.com",
        supported_params=[],
        job_id_pattern=r"-(\d+)$",
    )
    match = re.search(defn.job_id_pattern, "https://example.com/jobs/engineer-12345")
    assert match is not None
    assert match.group(1) == "12345"
