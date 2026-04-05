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
