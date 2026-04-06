"""Integration tests for LinkedInApplyAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

@pytest.fixture
def adapter():
    from src.automation.motors.crawl4ai.portals.linkedin.apply import LinkedInApplyAdapter

    return LinkedInApplyAdapter()


def test_source_name(adapter):
    assert adapter.source_name == "linkedin"


def test_session_profile_dir(adapter):
    assert "linkedin" in str(adapter.get_session_profile_dir()).lower()


def test_portal_map_loading(adapter):
    assert adapter.portal_map.portal_name == "linkedin"
    assert "job_details" in adapter.portal_map.states
    assert "standard_easy_apply" in adapter.portal_map.paths


def test_get_portal_base_url(adapter):
    assert "linkedin.com" in adapter._get_portal_base_url()


def test_get_success_text_not_empty(adapter):
    assert adapter.get_success_text().strip()
