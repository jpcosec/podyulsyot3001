from __future__ import annotations

from src.core.scraping.adapters.stepstone import StepStoneAdapter


def test_stepstone_extract_job_id_from_inline_url() -> None:
    adapter = StepStoneAdapter()
    url = "https://www.stepstone.de/stellenangebote--Data-Scientist-Berlin-Test--13722274-inline.html"
    assert adapter.extract_job_id(url) == "13722274"


def test_stepstone_build_detail_url() -> None:
    adapter = StepStoneAdapter()
    assert (
        adapter.build_detail_url("13722274")
        == "https://www.stepstone.de/stellenangebote--x--13722274-inline.html"
    )
    assert adapter.build_detail_url("abc") is None
