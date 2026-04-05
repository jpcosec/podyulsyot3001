"""Tests for BrowserOS playbook models."""

from __future__ import annotations

from pathlib import Path

from src.automation.motors.browseros.cli.models import BrowserOSPlaybook


def test_browseros_playbook_fixture_parses():
    playbook_path = Path("src/automation/motors/browseros/cli/traces/linkedin_easy_apply_v1.json")
    playbook = BrowserOSPlaybook.model_validate_json(
        playbook_path.read_text(encoding="utf-8")
    )

    assert playbook.meta.source == "linkedin"
    assert playbook.path == "linkedin.easy_apply.standard"
    assert len(playbook.steps) == 5
    assert playbook.steps[-1].dry_run_stop is True
