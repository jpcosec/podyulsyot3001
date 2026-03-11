"""Tests for graph control-plane state helpers."""

from __future__ import annotations

from src.core.graph.state import build_thread_id


def test_build_thread_id_uses_source_and_job_id() -> None:
    assert build_thread_id("linkedin", "201397") == "linkedin_201397"
