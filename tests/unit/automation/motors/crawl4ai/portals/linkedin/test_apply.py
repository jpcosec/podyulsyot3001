"""Integration tests for LinkedInApplyAdapter against HTML snapshots."""

from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FIXTURE_PATH = Path("tests/fixtures/apply/linkedin_apply_modal.html")


@pytest.fixture
def linkedin_html() -> str:
    if not FIXTURE_PATH.exists():
        pytest.skip(
            f"LinkedIn fixture not found at {FIXTURE_PATH}. "
            "Run: python scripts/capture_linkedin_apply_fixture.py --job-url <URL>"
        )
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def adapter():
    from src.automation.motors.crawl4ai.portals.linkedin.apply import LinkedInApplyAdapter

    return LinkedInApplyAdapter()


def test_source_name(adapter):
    assert adapter.source_name == "linkedin"


def test_session_profile_dir(adapter):
    assert "linkedin" in str(adapter.get_session_profile_dir()).lower()


def test_get_form_selectors_returns_all_mandatory(adapter):
    selectors = adapter.get_form_selectors()
    assert selectors.apply_button
    assert selectors.cv_upload
    assert selectors.submit_button
    assert selectors.success_indicator


def test_mandatory_selectors_found_in_fixture(adapter, linkedin_html):
    soup = BeautifulSoup(linkedin_html, "html.parser")
    selectors = adapter.get_form_selectors()
    for field in ("apply_button", "cv_upload", "submit_button"):
        sel = getattr(selectors, field)
        assert soup.select(sel), (
            f"Mandatory selector '{field}' not found in LinkedIn fixture"
        )


def test_optional_selectors_found_in_fixture(adapter, linkedin_html):
    soup = BeautifulSoup(linkedin_html, "html.parser")
    selectors = adapter.get_form_selectors()
    for field in ["first_name", "last_name", "email", "phone", "letter_upload"]:
        sel = getattr(selectors, field)
        if sel is None:
            continue
        assert soup.select(sel), (
            f"Optional selector '{field}' not found in LinkedIn fixture"
        )


def test_open_modal_script_is_idempotent(adapter):
    assert "IF NOT" in adapter.get_open_modal_script()


def test_fill_form_script_uses_placeholders(adapter):
    profile = {"first_name": "Alice", "last_name": "Smith", "email": "a@b.com"}
    script = adapter.get_fill_form_script(profile)
    assert "{{" in script
    assert "Alice" not in script
    assert "Smith" not in script


def test_render_script_injects_values(adapter):
    profile = {"first_name": "Alice", "last_name": "Smith"}
    template = adapter.get_fill_form_script(profile)
    rendered = adapter._render_script(template, profile)
    assert "{{first_name}}" not in rendered
    assert "{{last_name}}" not in rendered


def test_get_portal_base_url(adapter):
    assert "linkedin.com" in adapter._get_portal_base_url()


def test_get_success_text_not_empty(adapter):
    assert adapter.get_success_text().strip()
