"""Integration tests for XingApplyAdapter against HTML snapshots.

These tests load a saved HTML fixture and verify that the adapter's selectors
find the expected elements. They run without a live browser.

If the fixture file is missing, tests are skipped with a clear message.
Update the fixture by running: python scripts/capture_xing_apply_fixture.py
"""
from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FIXTURE_PATH = Path("tests/fixtures/apply/xing_apply_modal.html")


@pytest.fixture
def xing_html() -> str:
    if not FIXTURE_PATH.exists():
        pytest.skip(
            f"XING fixture not found at {FIXTURE_PATH}. "
            "Run: python scripts/capture_xing_apply_fixture.py --job-url <URL>"
        )
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def adapter():
    from src.automation.motors.crawl4ai.portals.xing.apply import XingApplyAdapter
    return XingApplyAdapter()


def test_source_name(adapter):
    assert adapter.source_name == "xing"


def test_session_profile_dir(adapter):
    assert "xing" in str(adapter.get_session_profile_dir()).lower()


def test_get_form_selectors_returns_all_mandatory(adapter):
    """FormSelectors has all four mandatory fields populated."""
    selectors = adapter.get_form_selectors()
    assert selectors.apply_button
    assert selectors.cv_upload
    assert selectors.submit_button
    assert selectors.success_indicator


def test_mandatory_selectors_found_in_fixture(adapter, xing_html):
    """Mandatory selectors match elements in the real XING apply modal HTML."""
    soup = BeautifulSoup(xing_html, "html.parser")
    selectors = adapter.get_form_selectors()
    for field in ("apply_button", "cv_upload", "submit_button"):
        sel = getattr(selectors, field)
        match = soup.select(sel)
        assert match, (
            f"Mandatory selector '{field}' = '{sel}' not found in XING fixture. "
            "DOM may have changed — re-capture fixture and update selectors."
        )


def test_optional_selectors_found_in_fixture(adapter, xing_html):
    """Optional selectors that are set should also be findable in the fixture."""
    soup = BeautifulSoup(xing_html, "html.parser")
    selectors = adapter.get_form_selectors()
    optional_fields = ["first_name", "last_name", "email", "phone", "letter_upload"]
    for field in optional_fields:
        sel = getattr(selectors, field)
        if sel is None:
            continue
        match = soup.select(sel)
        assert match, (
            f"Optional selector '{field}' = '{sel}' not found in XING fixture. "
            "Update the selector or set it to None if the field is absent."
        )


def test_open_modal_script_is_idempotent(adapter):
    """get_open_modal_script() contains an idempotency guard (IF NOT check)."""
    script = adapter.get_open_modal_script()
    assert "IF NOT" in script, (
        "Open modal script must check if modal is already open before clicking."
    )


def test_fill_form_script_uses_placeholders(adapter):
    """get_fill_form_script() uses {{placeholder}} syntax, not f-string values."""
    profile = {"first_name": "Alice", "last_name": "Smith", "email": "a@b.com"}
    script = adapter.get_fill_form_script(profile)
    # Script should contain placeholder markers, not the raw values
    assert "{{" in script, (
        "get_fill_form_script() must use {{placeholder}} syntax. "
        "Do not interpolate profile values directly — let _render_script() handle escaping."
    )
    assert "Alice" not in script
    assert "Smith" not in script


def test_render_script_injects_values(adapter):
    """_render_script() correctly substitutes placeholders with profile values."""
    profile = {"first_name": "Alice", "last_name": "Smith"}
    template = adapter.get_fill_form_script(profile)
    rendered = adapter._render_script(template, profile)
    assert "{{first_name}}" not in rendered
    assert "{{last_name}}" not in rendered


def test_get_portal_base_url(adapter):
    assert "xing.com" in adapter._get_portal_base_url()


def test_get_success_text_not_empty(adapter):
    assert adapter.get_success_text().strip()
