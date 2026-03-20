from __future__ import annotations

from src.core.scraping.registry import TuBerlinAdapter


def test_tu_berlin_extract_job_id() -> None:
    adapter = TuBerlinAdapter()
    url = "https://www.jobs.tu-berlin.de/en/job-postings/201588"
    assert adapter.extract_job_id(url) == "201588"


def test_tu_berlin_build_detail_url() -> None:
    adapter = TuBerlinAdapter()
    assert (
        adapter.build_detail_url("201588")
        == "https://www.jobs.tu-berlin.de/en/job-postings/201588"
    )
    assert adapter.build_detail_url("job-x") is None
