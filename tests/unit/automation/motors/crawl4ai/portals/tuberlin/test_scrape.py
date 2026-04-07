from types import SimpleNamespace

from src.automation.motors.crawl4ai.portals.tuberlin.scrape import TUBerlinAdapter


def test_source_name():
    assert TUBerlinAdapter().source_name == "tuberlin"


def test_supported_params():
    adapter = TUBerlinAdapter()
    assert "categories" in adapter.supported_params
    assert "job_query" in adapter.supported_params


def test_extract_job_id():
    adapter = TUBerlinAdapter()
    url = "https://www.jobs.tu-berlin.de/en/job-postings/11223344"
    assert adapter.extract_job_id(url) == "11223344"


def test_extract_links_returns_structured_entries():
    adapter = TUBerlinAdapter()
    crawl_result = SimpleNamespace(
        links={
            "internal": [
                {
                    "href": "/en/job-postings/11223344",
                    "text": "Research Assistant",
                    "title": "Research Assistant Job",
                },
                {
                    "href": "/en/job-postings/11223344/apply",
                    "text": "Apply",
                },
            ]
        }
    )

    links = adapter.extract_links(crawl_result)

    assert len(links) == 1
    assert links[0].url == "https://www.jobs.tu-berlin.de/en/job-postings/11223344"
    assert links[0].job_id == "11223344"
    assert links[0].listing_position == 0
    assert links[0].listing_snippet == "Research Assistant"
