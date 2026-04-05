"""Tests that scrape portal definitions are valid and contain expected data."""
from __future__ import annotations

import re

from src.automation.ariadne.portal_models import ScrapePortalDefinition


def _assert_valid_regex(pattern: str, sample_url: str, expected_id: str) -> None:
    match = re.search(pattern, sample_url)
    assert match is not None, f"Pattern {pattern!r} did not match {sample_url!r}"
    assert match.group(1) == expected_id


def test_stepstone_scrape_portal():
    from src.automation.portals.stepstone.scrape import STEPSTONE_SCRAPE

    assert isinstance(STEPSTONE_SCRAPE, ScrapePortalDefinition)
    assert STEPSTONE_SCRAPE.source_name == "stepstone"
    assert STEPSTONE_SCRAPE.base_url == "https://www.stepstone.de"
    assert "job_query" in STEPSTONE_SCRAPE.supported_params
    assert "city" in STEPSTONE_SCRAPE.supported_params
    assert "max_days" in STEPSTONE_SCRAPE.supported_params
    _assert_valid_regex(
        STEPSTONE_SCRAPE.job_id_pattern,
        "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html",
        "12345678",
    )


def test_xing_scrape_portal():
    from src.automation.portals.xing.scrape import XING_SCRAPE

    assert isinstance(XING_SCRAPE, ScrapePortalDefinition)
    assert XING_SCRAPE.source_name == "xing"
    assert XING_SCRAPE.base_url == "https://www.xing.com"
    assert "job_query" in XING_SCRAPE.supported_params
    assert "city" in XING_SCRAPE.supported_params
    assert "max_days" in XING_SCRAPE.supported_params
    _assert_valid_regex(
        XING_SCRAPE.job_id_pattern,
        "https://www.xing.com/jobs/berlin-data-engineer-9876543",
        "9876543",
    )


def test_tuberlin_scrape_portal():
    from src.automation.portals.tuberlin.scrape import TUBERLIN_SCRAPE

    assert isinstance(TUBERLIN_SCRAPE, ScrapePortalDefinition)
    assert TUBERLIN_SCRAPE.source_name == "tuberlin"
    assert TUBERLIN_SCRAPE.base_url == "https://www.jobs.tu-berlin.de"
    assert "categories" in TUBERLIN_SCRAPE.supported_params
    assert "job_query" in TUBERLIN_SCRAPE.supported_params
    _assert_valid_regex(
        TUBERLIN_SCRAPE.job_id_pattern,
        "https://www.jobs.tu-berlin.de/en/job-postings/11223344",
        "11223344",
    )
