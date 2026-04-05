from src.automation.motors.crawl4ai.portals.xing.scrape import XingAdapter

def test_source_name():
    assert XingAdapter().source_name == "xing"

def test_extract_job_id():
    adapter = XingAdapter()
    url = "https://www.xing.com/jobs/berlin-data-engineer-9876543"
    assert adapter.extract_job_id(url) == "9876543"
