"""Unit tests for ApplyAdapter pure logic helpers.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from src.automation.ariadne.models import AriadnePortalMap
from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter


class _ConcreteAdapter(ApplyAdapter):
    """Minimal concrete implementation for testing the base class."""

    @property
    def portal_map(self) -> AriadnePortalMap:
        return AriadnePortalMap(
            portal_name="test_portal",
            base_url="https://test.example.com",
            states={},
            tasks={},
            paths={}
        )

    def get_success_text(self) -> str:
        return "Application submitted"

    def get_session_profile_dir(self):
        return Path("data/profiles/test_profile")


class TestRenderPlaceholders:
    def test_basic_interpolation(self):
        """_render_placeholders substitutes {{placeholders}} with context values."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{first_name}}"'
        result = adapter._render_placeholders(template, {"first_name": "Alice"})
        assert result == 'SET `input` "Alice"'

    def test_nested_interpolation(self):
        """_render_placeholders supports nested profile.key access."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{profile.first_name}}"'
        result = adapter._render_placeholders(template, {"profile": {"first_name": "Alice"}})
        assert result == 'SET `input` "Alice"'

    def test_unused_placeholder_preserved(self):
        """Placeholders with no matching key are left as-is."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{first_name}}" "{{unknown}}"'
        result = adapter._render_placeholders(template, {"first_name": "Alice"})
        assert "Alice" in result
        assert "{{unknown}}" in result


class TestIdempotency:
    def test_check_idempotency_no_prior_artifact(self, tmp_path):
        """No exception when no prior apply_meta.json exists."""
        from src.automation.storage import AutomationStorage
        from src.core.data_manager import DataManager
        storage = AutomationStorage(DataManager(tmp_path / "data" / "jobs"))
        adapter = _ConcreteAdapter(storage)
        adapter._check_idempotency("99999")  # no exception

    def test_check_idempotency_submitted_raises(self, tmp_path):
        """RuntimeError raised when prior apply was submitted."""
        from src.automation.storage import AutomationStorage
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
        storage = AutomationStorage(manager)
        adapter = _ConcreteAdapter(storage)
        with pytest.raises(RuntimeError, match="already submitted"):
            adapter._check_idempotency("99999")
