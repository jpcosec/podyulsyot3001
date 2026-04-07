"""Validate the LinkedIn easy_apply Ariadne map."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.automation.ariadne.models import AriadnePortalMap

_MAP_PATH = Path("src/automation/portals/linkedin/maps/easy_apply.json")


@pytest.fixture(scope="module")
def portal_map() -> AriadnePortalMap:
    return AriadnePortalMap.model_validate(json.loads(_MAP_PATH.read_text()))


def test_portal_name(portal_map):
    assert portal_map.portal_name == "linkedin"


def test_required_states_present(portal_map):
    assert "job_details" in portal_map.states


def test_standard_path_present(portal_map):
    assert "standard_easy_apply" in portal_map.paths


def test_success_criteria(portal_map):
    task = portal_map.tasks["submit_easy_apply"]
    assert task.success_criteria.get("text_match") == "application"
