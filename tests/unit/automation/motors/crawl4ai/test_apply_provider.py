"""Unit tests for C4AIReplayer pure logic helpers.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from src.automation.motors.crawl4ai.replayer import C4AIReplayer


class TestRenderPlaceholders:
    def test_basic_interpolation(self):
        """_render_placeholders substitutes {{placeholders}} with context values."""
        replayer = C4AIReplayer()
        template = 'SET `input` "{{first_name}}"'
        result = replayer._render_placeholders(template, {"first_name": "Alice"})
        assert result == 'SET `input` "Alice"'

    def test_nested_interpolation(self):
        """_render_placeholders supports nested profile.key access."""
        replayer = C4AIReplayer()
        template = 'SET `input` "{{profile.first_name}}"'
        result = replayer._render_placeholders(template, {"profile": {"first_name": "Alice"}})
        assert result == 'SET `input` "Alice"'
