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


def test_all_step_state_ids_reference_valid_states(portal_map):
    path = portal_map.paths["standard_easy_apply"]
    state_ids = set(portal_map.states.keys())
    for step in path.steps:
        assert step.state_id in state_ids, (
            f"Step '{step.name}' references unknown state '{step.state_id}'"
        )


def test_task_entry_and_success_states_exist(portal_map):
    task = portal_map.tasks["submit_easy_apply"]
    assert task.entry_state in portal_map.states
    for state in task.success_states:
        assert state in portal_map.states


def test_path_task_id_references_valid_task(portal_map):
    path = portal_map.paths["standard_easy_apply"]
    assert path.task_id in portal_map.tasks


def test_all_steps_have_observe_and_actions(portal_map):
    path = portal_map.paths["standard_easy_apply"]
    for step in path.steps:
        assert step.observe is not None, f"Step '{step.name}' has no observe block"
        assert step.actions, f"Step '{step.name}' has no actions"


def test_final_step_has_dry_run_stop(portal_map):
    path = portal_map.paths["standard_easy_apply"]
    final_step = path.steps[-1]
    assert final_step.dry_run_stop is True, (
        "Final apply step must have dry_run_stop=True"
    )
