"""Tests that apply portal definitions are valid and contain expected data."""
from __future__ import annotations

from src.automation.ariadne.portal_models import ApplyPortalDefinition, FieldType


def _get_field(defn: ApplyPortalDefinition, step_name: str, field_name: str):
    step = next(s for s in defn.steps if s.name == step_name)
    return next(f for f in step.fields if f.name == field_name)


def test_linkedin_apply_portal():
    from src.automation.portals.linkedin.apply import LINKEDIN_APPLY

    assert isinstance(LINKEDIN_APPLY, ApplyPortalDefinition)
    assert LINKEDIN_APPLY.source_name == "linkedin"
    assert LINKEDIN_APPLY.base_url == "https://www.linkedin.com"
    step_names = [s.name for s in LINKEDIN_APPLY.steps]
    assert "open_modal" in step_names
    assert "upload_cv" in step_names
    assert "submit" in step_names
    cv_field = _get_field(LINKEDIN_APPLY, "upload_cv", "cv")
    assert cv_field.field_type == FieldType.FILE_PDF
    assert cv_field.required is True
    submit_step = next(s for s in LINKEDIN_APPLY.steps if s.name == "submit")
    assert submit_step.dry_run_stop is True


def test_stepstone_apply_portal():
    from src.automation.portals.stepstone.apply import STEPSTONE_APPLY

    assert isinstance(STEPSTONE_APPLY, ApplyPortalDefinition)
    assert STEPSTONE_APPLY.source_name == "stepstone"
    assert STEPSTONE_APPLY.base_url == "https://www.stepstone.de"
    step_names = [s.name for s in STEPSTONE_APPLY.steps]
    assert "submit" in step_names
    submit_step = next(s for s in STEPSTONE_APPLY.steps if s.name == "submit")
    assert submit_step.dry_run_stop is True


def test_xing_apply_portal():
    from src.automation.portals.xing.apply import XING_APPLY

    assert isinstance(XING_APPLY, ApplyPortalDefinition)
    assert XING_APPLY.source_name == "xing"
    assert XING_APPLY.base_url == "https://www.xing.com"
    step_names = [s.name for s in XING_APPLY.steps]
    assert "submit" in step_names
