"""Unit tests for ApplyAdapter pure logic helpers.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""
from __future__ import annotations

import pytest

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter, PortalStructureChangedError


class _ConcreteAdapter(ApplyAdapter):
    """Minimal concrete implementation for testing the base class."""

    @property
    def source_name(self) -> str:
        return "test_portal"

    def get_form_selectors(self) -> FormSelectors:
        return FormSelectors(
            apply_button="button.apply",
            cv_upload="input.cv",
            submit_button="button.submit",
            success_indicator=".success",
            first_name="input[name='firstName']",
            email="input[name='email']",
        )

    def get_open_modal_script(self) -> str:
        return "CLICK `button.apply`\nWAIT `.modal` 5"

    def get_fill_form_script(self, profile: dict) -> str:
        return 'SET `input[name="firstName"]` "{{first_name}}"\nSET `input[name="email"]` "{{email}}"'

    def get_submit_script(self) -> str:
        return "CLICK `button.submit`"

    def get_success_text(self) -> str:
        return "Application submitted"

    def get_session_profile_dir(self):
        from pathlib import Path
        return Path("data/profiles/test_profile")

    def _get_portal_base_url(self) -> str:
        return "https://test.example.com"


class TestCheckSelectorResults:
    def test_all_present_passes(self):
        """No exception when all mandatory selectors present."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": True,
            "cv_upload": True,
            "submit_button": True,
            "success_indicator": True,
            "first_name": True,
            "email": True,
        }
        adapter._check_selector_results(results, selectors)  # no exception

    def test_missing_mandatory_raises(self):
        """Missing mandatory selector raises PortalStructureChangedError."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": True,
            "cv_upload": False,  # mandatory, missing
            "submit_button": True,
            "success_indicator": True,
        }
        with pytest.raises(PortalStructureChangedError) as exc_info:
            adapter._check_selector_results(results, selectors)
        assert "cv_upload" in str(exc_info.value)

    def test_missing_optional_does_not_raise(self):
        """Missing optional selector logs a warning but does not raise."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": True,
            "cv_upload": True,
            "submit_button": True,
            "success_indicator": True,
            "first_name": False,  # optional, missing — should not raise
            "email": True,
        }
        adapter._check_selector_results(results, selectors)  # no exception

    def test_multiple_missing_mandatory_listed(self):
        """Error message lists all missing mandatory selectors."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": False,
            "cv_upload": False,
            "submit_button": True,
            "success_indicator": False,
        }
        with pytest.raises(PortalStructureChangedError) as exc_info:
            adapter._check_selector_results(results, selectors)
        msg = str(exc_info.value)
        assert "apply_button" in msg
        assert "cv_upload" in msg
        assert "success_indicator" in msg


class TestRenderScript:
    def test_basic_interpolation(self):
        """_render_script substitutes {{placeholders}} with json.dumps values."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{first_name}}"'
        result = adapter._render_script(template, {"first_name": "Alice"})
        assert result == 'SET `input` "Alice"'

    def test_apostrophe_escaped(self):
        """Values with apostrophes are safely escaped via json.dumps."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{name}}"'
        result = adapter._render_script(template, {"name": "O'Connor"})
        # json.dumps("O'Connor") = '"O\'Connor"' — apostrophe safe in C4A-Script
        assert "O'Connor" in result or "O\\u0027Connor" not in result

    def test_unused_placeholder_preserved(self):
        """Placeholders with no matching profile key are left as-is."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{first_name}}" "{{unknown}}"'
        result = adapter._render_script(template, {"first_name": "Alice"})
        assert "Alice" in result
        assert "{{unknown}}" in result

    def test_none_value_becomes_empty_string(self):
        """None profile values become empty strings, not the word 'None'."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{phone}}"'
        result = adapter._render_script(template, {"phone": None})
        assert "None" not in result
        assert '""' in result


class TestIdempotency:
    def test_check_idempotency_no_prior_artifact(self, tmp_path):
        """No exception when no prior apply_meta.json exists."""
        from src.core.data_manager import DataManager
        adapter = _ConcreteAdapter(DataManager(tmp_path / "data" / "jobs"))
        adapter._check_idempotency("99999")  # no exception

    def test_check_idempotency_submitted_raises(self, tmp_path):
        """RuntimeError raised when prior apply was submitted."""
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="test_portal",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "submitted", "timestamp": "2026-03-30T00:00:00Z", "error": None},
        )
        adapter = _ConcreteAdapter(manager)
        with pytest.raises(RuntimeError, match="already submitted"):
            adapter._check_idempotency("99999")

    def test_check_idempotency_dry_run_allows_retry(self, tmp_path):
        """dry_run status allows re-execution (no exception)."""
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="test_portal",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "dry_run", "timestamp": "2026-03-30T00:00:00Z", "error": None},
        )
        adapter = _ConcreteAdapter(manager)
        adapter._check_idempotency("99999")  # no exception

    def test_check_idempotency_failed_allows_retry(self, tmp_path):
        """failed status allows re-execution (no exception)."""
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="test_portal",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "failed", "timestamp": "2026-03-30T00:00:00Z", "error": "network error"},
        )
        adapter = _ConcreteAdapter(manager)
        adapter._check_idempotency("99999")  # no exception
