"""Integration tests for StepStone apply flow."""

from __future__ import annotations

from pathlib import Path
import pytest

@pytest.fixture
def provider():
    from src.automation.motors.crawl4ai.apply_engine import Crawl4AIApplyProvider
    return Crawl4AIApplyProvider("stepstone")


def test_source_name(provider):
    assert provider.source_name == "stepstone"


def test_portal_map_loading(provider):
    assert provider.portal_map.portal_name == "stepstone"
    assert "job_details" in provider.portal_map.states
    assert "standard_easy_apply" in provider.portal_map.paths


def test_success_criteria(provider):
    task = provider.portal_map.tasks["submit_easy_apply"]
    assert task.success_criteria.get("text_match") == "Bewerbung"
