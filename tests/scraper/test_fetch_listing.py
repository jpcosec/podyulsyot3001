import src.scraper.fetch_listing as fetch_listing
from src.scraper.fetch_listing import (
    build_page_url,
    collect_known_job_ids,
    crawl_listing,
    extract_job_urls_from_html,
)


SAMPLE_LISTING_HTML = """
<html><body>
<a href="/en/job-postings/12345?filter[worktype_tub][]=wiss-mlehr">Job A</a>
<a href="/en/job-postings/67890?filter[worktype_tub][]=wiss-olehr">Job B</a>
<a href="/en/job-postings">Overview</a>
<a href="/en/about">About</a>
</body></html>
"""


def test_extract_job_urls_from_html():
    result = extract_job_urls_from_html(SAMPLE_LISTING_HTML)
    assert result == {"12345", "67890"}


def test_extract_job_urls_empty_page():
    result = extract_job_urls_from_html("<html><body>No jobs</body></html>")
    assert result == set()


def test_collect_known_job_ids(tmp_path):
    source_dir = tmp_path / "tu_berlin"
    source_dir.mkdir()
    (source_dir / "201397").mkdir()
    (source_dir / "201399").mkdir()
    (source_dir / "summary.csv").touch()
    archive_dir = source_dir / "archive"
    archive_dir.mkdir()
    (archive_dir / "201084").mkdir()
    (archive_dir / "201084 1").mkdir()

    result = collect_known_job_ids(tmp_path, "tu_berlin")
    assert result == {"201397", "201399", "201084"}


def test_build_page_url_with_existing_query():
    url = "https://example.com/jobs?filter[x]=y"
    assert build_page_url(url, 2) == "https://example.com/jobs?filter[x]=y&page=2"


def test_build_page_url_no_query():
    url = "https://example.com/jobs"
    assert build_page_url(url, 3) == "https://example.com/jobs?page=3"


def test_build_page_url_replaces_existing_page_param():
    url = "https://example.com/jobs?filter[x]=y&page=1"
    assert build_page_url(url, 4) == "https://example.com/jobs?filter[x]=y&page=4"


def test_crawl_listing_scrapes_only_new_jobs(tmp_path, monkeypatch):
    source_dir = tmp_path / "tu_berlin"
    source_dir.mkdir()
    (source_dir / "100").mkdir()
    archive_dir = source_dir / "archive"
    archive_dir.mkdir()
    (archive_dir / "300").mkdir()

    page_html = {
        1: """
        <html><body>
        <a href="/en/job-postings/100">Job 100</a>
        <a href="/en/job-postings/200">Job 200</a>
        </body></html>
        """,
        2: """
        <html><body>
        <a href="/en/job-postings/200">Job 200</a>
        <a href="/en/job-postings/300">Job 300</a>
        </body></html>
        """,
        3: "<html><body>No jobs</body></html>",
    }

    def fake_download_html(url: str) -> str:
        if "page=1" in url:
            return page_html[1]
        if "page=2" in url:
            return page_html[2]
        if "page=3" in url:
            return page_html[3]
        raise AssertionError(f"Unexpected page URL: {url}")

    calls: list[dict[str, object]] = []

    def fake_run_for_url(
        url: str,
        source: str,
        pipeline_root,
        strict_english: bool,
    ) -> dict[str, str]:
        calls.append(
            {
                "url": url,
                "source": source,
                "pipeline_root": pipeline_root,
                "strict_english": strict_english,
            }
        )
        return {"job_id": url.rsplit("/", maxsplit=1)[-1]}

    monkeypatch.setattr(fetch_listing, "download_html", fake_download_html)
    monkeypatch.setattr(fetch_listing, "run_for_url", fake_run_for_url)
    monkeypatch.setattr(fetch_listing.time, "sleep", lambda _seconds: None)

    result = crawl_listing(
        listing_url="https://www.jobs.tu-berlin.de/en/job-postings?filter[x]=y",
        source="tu_berlin",
        pipeline_root=tmp_path,
        strict_english=True,
        delay=0,
    )

    assert result == {
        "scraped": ["200"],
        "skipped": ["100", "300"],
        "failed": [],
    }
    assert len(calls) == 1
    assert calls[0]["url"] == "https://www.jobs.tu-berlin.de/en/job-postings/200"
    assert calls[0]["source"] == "tu_berlin"
    assert calls[0]["pipeline_root"] == tmp_path
    assert calls[0]["strict_english"] is True
