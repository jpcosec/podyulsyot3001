"""Tests for portal mode config caching and registry reuse."""

from __future__ import annotations

from pathlib import Path

from src.automation.ariadne.modes.registry import ModeRegistry
from src.automation.portals.modes.portals import JsonConfigMode, LinkedInMode


def test_json_config_mode_uses_preloaded_cache(monkeypatch):
    """JsonConfigMode should read configs once and reuse the cache."""
    JsonConfigMode._config_cache = {}
    JsonConfigMode._configs_loaded = False

    open_calls: list[str] = []
    original_open = Path.open

    def tracking_open(self, *args, **kwargs):
        open_calls.append(str(self))
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)

    JsonConfigMode.preload_configs()
    first_config = JsonConfigMode.get_config("linkedin")
    second_config = JsonConfigMode.get_config("linkedin")

    assert first_config == second_config
    assert first_config["selectors"]["apply_button"] == "button.jobs-apply-button"
    assert sum(path.endswith("linkedin.json") for path in open_calls) == 1


def test_mode_registry_reuses_preloaded_mode_instances():
    """ModeRegistry should return cached mode instances after discovery."""
    ModeRegistry._mapping = {}
    ModeRegistry._loaded = False
    ModeRegistry._default_mode = None
    JsonConfigMode._config_cache = {
        "linkedin": {"selectors": {"apply_button": "button.jobs-apply-button"}}
    }
    JsonConfigMode._configs_loaded = True

    first_mode = ModeRegistry.get_mode_for_url("https://www.linkedin.com/jobs/view/1")
    second_mode = ModeRegistry.get_mode_for_url("https://www.linkedin.com/jobs/view/2")

    assert isinstance(first_mode, LinkedInMode)
    assert first_mode is second_mode
    assert first_mode.config["selectors"]["apply_button"] == "button.jobs-apply-button"
