import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

from src.automation.motors.crawl4ai.portals.xing.scrape import XingAdapter


def test_source_name():
    assert XingAdapter().source_name == "xing"


def test_extract_job_id():
    adapter = XingAdapter()
    url = "https://www.xing.com/jobs/berlin-data-engineer-9876543"
    assert adapter.extract_job_id(url) == "9876543"


def test_extract_links_returns_url_key():
    """extract_links must return structured entries for the scrape engine."""
    adapter = XingAdapter()
    html = (
        "<html><body>"
        '<article class="job-card">'
        '<a href="https://www.xing.com/jobs/berlin-data-engineer-1234567" title="Data Engineer">'
        "<h2>Data Engineer</h2>"
        "</a>"
        '<p class="company">Example Co</p>'
        '<p class="location">Berlin</p>'
        '<p class="salary">EUR 70.000</p>'
        '<p class="employment">Full-time</p>'
        '<time datetime="2026-04-05">vor 2 Tagen</time>'
        "</article>"
        '<article class="job-card">'
        '<a href="https://www.xing.com/jobs/munich-ml-engineer-7654321">ML Engineer</a>'
        '<p class="company">Second Co</p>'
        "</article>"
        '<a href="https://www.xing.com/company/foo">Not a job</a>'
        "</body></html>"
    )
    crawl_result = SimpleNamespace(cleaned_html=html, html=html)
    links = adapter.extract_links(crawl_result)
    assert len(links) == 2
    assert links[0].url == "https://www.xing.com/jobs/berlin-data-engineer-1234567"
    assert links[0].job_id == "1234567"
    assert links[0].listing_position == 0
    assert "Example Co" in links[0].listing_snippet
    assert links[0].listing_data.job_title == "Data Engineer"
    assert links[0].listing_data.company_name == "Example Co"
    assert links[0].listing_data.location == "Berlin"
    assert links[0].listing_data.salary == "EUR 70.000"
    assert links[0].listing_data.employment_type == "Full-time"
    assert links[0].listing_data.posted_date == "vor 2 Tagen"
    assert "job-card" in links[0].model_extra["listing_case_cleaned_html"]


def _detail_result(payload: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(
        url="https://www.xing.com/jobs/berlin-data-engineer-1234567",
        success=True,
        extracted_content=json.dumps(payload),
        markdown=SimpleNamespace(
            fit_markdown="# Data Engineer\nBuild pipelines",
            raw_markdown="# Data Engineer",
        ),
        html="<html><body>detail</body></html>",
        cleaned_html="<html><body>detail</body></html>",
        error_message=None,
        crawl_stats={},
        status_code=200,
    )


def test_extract_payload_merges_xing_listing_metadata_before_validation():
    adapter = XingAdapter()
    listing_html = (
        "<html><body>"
        '<article class="job-card">'
        '<a href="https://www.xing.com/jobs/berlin-data-engineer-1234567">'
        "<h2>Data Engineer</h2>"
        "</a>"
        '<p class="company">Example Co</p>'
        '<p class="location">Berlin</p>'
        '<p class="salary">EUR 70.000</p>'
        '<p class="employment">Full-time</p>'
        '<time datetime="2026-04-05">vor 2 Tagen</time>'
        "</article>"
        "</body></html>"
    )
    discovery_entry = adapter.extract_links(
        SimpleNamespace(cleaned_html=listing_html, html=listing_html)
    )[0]
    detail_payload = {
        "job_title": "Data Engineer",
        "company_name": "Example Co",
        "location": "Berlin",
        "employment_type": "Full-time",
        "responsibilities": ["Build pipelines"],
        "requirements": ["Python"],
    }

    valid_data, cleaned_payload, css_payload, extraction_method, extraction_error = asyncio.run(
        adapter._extract_payload(
            _detail_result(detail_payload),
            discovery_entry=discovery_entry,
            scraped_at=datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc),
        )
    )

    assert extraction_error is None
    assert extraction_method == "css"
    assert valid_data is not None
    assert cleaned_payload is not None
    assert valid_data["posted_date"] == "2026-04-05T12:00:00+00:00"
    assert valid_data["days_ago"] == "vor 2 Tagen"
    assert cleaned_payload["listing_case"]["teaser_salary"] == "EUR 70.000"
    assert cleaned_payload["listing_case"]["teaser_company"] == "Example Co"
