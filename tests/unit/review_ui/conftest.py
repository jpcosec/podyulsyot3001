"""Pytest configuration for review_ui tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
