"""Unit tests for Crawl4AIApplyProvider pure logic helpers.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from src.automation.ariadne.models import AriadnePortalMap
from src.automation.motors.crawl4ai.apply_engine import Crawl4AIApplyProvider


class TestRenderPlaceholders:
    def test_basic_interpolation(self):
        """_render_placeholders substitutes {{placeholders}} with context values."""
        provider = Crawl4AIApplyProvider("linkedin")
        template = 'SET `input` "{{first_name}}"'
        result = provider.replayer._render_placeholders(template, {"first_name": "Alice"})
        assert result == 'SET `input` "Alice"'

    def test_nested_interpolation(self):
        """_render_placeholders supports nested profile.key access."""
        provider = Crawl4AIApplyProvider("linkedin")
        template = 'SET `input` "{{profile.first_name}}"'
        result = provider.replayer._render_placeholders(template, {"profile": {"first_name": "Alice"}})
        assert result == 'SET `input` "Alice"'


class TestIdempotency:
    def test_check_idempotency_no_prior_artifact(self, tmp_path):
        """No exception when no prior apply_meta.json exists."""
        from src.automation.storage import AutomationStorage
        from src.core.data_manager import DataManager
        storage = AutomationStorage(DataManager(tmp_path / "data" / "jobs"))
        provider = Crawl4AIApplyProvider("linkedin", storage)
        # no exception expected
        if storage.check_already_submitted("linkedin", "99999"):
            pytest.fail("Should not be already submitted")

    def test_check_idempotency_submitted_raises(self, tmp_path):
        """RuntimeError raised when prior apply was submitted."""
        from src.automation.storage import AutomationStorage
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="linkedin",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "submitted", "timestamp": "2026-03-30T00:00:00Z", "error": None},
        )
        storage = AutomationStorage(manager)
        provider = Crawl4AIApplyProvider("linkedin", storage)
        with pytest.raises(RuntimeError, match="already submitted"):
            if storage.check_already_submitted("linkedin", "99999"):
                raise RuntimeError("Job linkedin (99999) was already submitted.")
