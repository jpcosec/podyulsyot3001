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
    url = "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html"
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
