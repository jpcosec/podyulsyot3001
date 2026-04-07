from types import SimpleNamespace

from src.automation.motors.crawl4ai.portals.stepstone.scrape import StepStoneAdapter


def test_source_name():
    adapter = StepStoneAdapter()
    assert adapter.source_name == "stepstone"


def test_supported_params():
    adapter = StepStoneAdapter()
    assert "job_query" in adapter.supported_params
    assert "city" in adapter.supported_params
    assert "max_days" in adapter.supported_params


def test_extract_job_id():
    adapter = StepStoneAdapter()
    url = (
        "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html"
    )
    assert adapter.extract_job_id(url) == "12345678"


def test_extract_job_id_unknown():
    adapter = StepStoneAdapter()
    assert adapter.extract_job_id("https://www.stepstone.de/no-match") == "unknown"


def test_get_search_url_default():
    adapter = StepStoneAdapter()
    url = adapter.get_search_url(job_query="data scientist", city="berlin")
    assert "stepstone.de" in url
    assert "data-scientist" in url
    assert "berlin" in url


def test_extract_links_returns_structured_entries():
    adapter = StepStoneAdapter()
    crawl_result = SimpleNamespace(
        links={
            "internal": [
                {
                    "href": "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html",
                    "text": "Data Engineer",
                    "title": "Data Engineer at Example Co",
                },
                {
                    "href": "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html",
                    "text": "Duplicate",
                },
            ],
            "external": [],
        }
    )

    links = adapter.extract_links(crawl_result)

    assert len(links) == 1
    assert links[0].url.endswith("12345678-inline.html")
    assert links[0].job_id == "12345678"
    assert links[0].listing_position == 0
    assert links[0].listing_snippet == "Data Engineer"
    assert links[0].listing_data.job_title == "Data Engineer"
