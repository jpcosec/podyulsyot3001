from __future__ import annotations

import pytest

from src.core.scraping.contracts import ScrapeDetailResult
from src.nodes.scrape.logic import run_logic


def test_run_logic_populates_ingested_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.nodes.scrape.logic.scrape_detail",
        lambda _request: ScrapeDetailResult(
            canonical_scrape={
                "source": "tu_berlin",
                "source_url": "https://example.org/job/1",
                "resolved_url": "https://example.org/job/1",
                "job_id": "job-1",
                "raw_text": "Python role details",
                "original_language": "en",
                "metadata": {"marker_hits": 0},
                "warnings": [],
                "artifact_refs": {"canonical_scrape": "a/b.json"},
            },
            artifact_refs={"canonical_scrape": "a/b.json"},
            warnings=["ok"],
            used_fetch_mode="http",
        ),
    )

    out = run_logic(
        {
            "source": "tu_berlin",
            "source_url": "https://example.org/job/1",
            "job_id": "job-1",
        }
    )

    assert out["current_node"] == "scrape"
    assert out["status"] == "running"
    assert out["ingested_data"]["source_url"] == "https://example.org/job/1"
    assert out["ingested_data"]["original_language"] == "en"
    assert out["ingested_data"]["raw_text"] == "Python role details"
    assert (
        out["ingested_data"]["metadata"]["artifact_refs"]["canonical_scrape"]
        == "a/b.json"
    )


def test_run_logic_requires_source_url() -> None:
    with pytest.raises(ValueError, match="source_url"):
        run_logic({"job_id": "job-1"})
