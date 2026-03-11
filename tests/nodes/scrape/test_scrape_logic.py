"""Tests for scrape ingestion logic."""

from __future__ import annotations

import pytest

from src.nodes.scrape.logic import run_logic


def test_run_logic_populates_ingested_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.nodes.scrape.logic.fetch_html",
        lambda _url: "<html><body><h1>Python role</h1></body></html>",
    )
    monkeypatch.setattr(
        "src.nodes.scrape.logic.extract_source_text_markdown",
        lambda html, url: f"# Scraped\nURL: {url}\n{html}",
    )
    monkeypatch.setattr(
        "src.nodes.scrape.logic.detect_english_status",
        lambda _md: {"is_english": True, "marker_hits": 0, "has_umlaut": False},
    )

    out = run_logic({"source_url": "https://example.org/job/1", "job_id": "job-1"})

    assert out["current_node"] == "scrape"
    assert out["status"] == "running"
    assert out["ingested_data"]["source_url"] == "https://example.org/job/1"
    assert out["ingested_data"]["original_language"] == "en"


def test_run_logic_requires_source_url() -> None:
    with pytest.raises(ValueError, match="source_url"):
        run_logic({"job_id": "job-1"})
