"""Integration tests for StepStoneApplyAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

@pytest.fixture
def adapter():
    from src.automation.motors.crawl4ai.portals.stepstone.apply import StepStoneApplyAdapter
    return StepStoneApplyAdapter()


def test_source_name(adapter):
    assert adapter.source_name == "stepstone"


def test_session_profile_dir(adapter):
    assert "stepstone" in str(adapter.get_session_profile_dir()).lower()


def test_portal_map_loading(adapter):
    assert adapter.portal_map.portal_name == "stepstone"
    assert "job_details" in adapter.portal_map.states
    assert "standard_easy_apply" in adapter.portal_map.paths


def test_get_portal_base_url(adapter):
    assert "stepstone.de" in adapter._get_portal_base_url().lower()


def test_get_success_text_not_empty(adapter):
    assert adapter.get_success_text().strip()
