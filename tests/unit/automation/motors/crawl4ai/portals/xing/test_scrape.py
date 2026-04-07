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
        '<a href="https://www.xing.com/jobs/berlin-data-engineer-1234567" title="Data Engineer">Data Engineer</a>'
        '<a href="https://www.xing.com/jobs/munich-ml-engineer-7654321">ML Engineer</a>'
        '<a href="https://www.xing.com/company/foo">Not a job</a>'
        "</body></html>"
    )
    crawl_result = SimpleNamespace(cleaned_html=html, html=html)
    links = adapter.extract_links(crawl_result)
    assert len(links) == 2
    assert links[0].url == "https://www.xing.com/jobs/berlin-data-engineer-1234567"
    assert links[0].job_id == "1234567"
    assert links[0].listing_position == 0
    assert links[0].listing_snippet == "Data Engineer"
    assert links[0].listing_data.job_title == "Data Engineer"
