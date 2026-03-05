from __future__ import annotations

from src.core.tools.scraping.service import (
    build_listing_page_url,
    crawl_listing,
    detect_english_status,
    extract_job_ids_from_listing_html,
)


def test_build_listing_page_url_appends_page_parameter() -> None:
    assert (
        build_listing_page_url("https://example.com/jobs", 2)
        == "https://example.com/jobs?page=2"
    )
    assert (
        build_listing_page_url("https://example.com/jobs?kind=phd", 3)
        == "https://example.com/jobs?kind=phd&page=3"
    )


def test_build_listing_page_url_replaces_existing_page_parameter() -> None:
    assert (
        build_listing_page_url("https://example.com/jobs?page=1&kind=phd", 4)
        == "https://example.com/jobs?page=4&kind=phd"
    )


def test_extract_job_ids_from_listing_html() -> None:
    html = """
    <a href="/en/job-postings/12345">A</a>
    <a href="/job-postings/67890">B</a>
    <a href="/job-postings/not-a-number">C</a>
    """
    assert extract_job_ids_from_listing_html(html) == {"12345", "67890"}


def test_crawl_listing_discovers_only_new_ids() -> None:
    pages = {
        "https://example.com/jobs?page=1": '<a href="/job-postings/100">A</a><a href="/job-postings/101">B</a>',
        "https://example.com/jobs?page=2": '<a href="/job-postings/101">B</a><a href="/job-postings/102">C</a>',
        "https://example.com/jobs?page=3": "",
    }

    def fake_fetch(url: str) -> str:
        return pages[url]

    result = crawl_listing(
        "https://example.com/jobs",
        known_job_ids={"100"},
        max_pages=10,
        fetch_html_fn=fake_fetch,
    )

    assert result.discovered_ids == ["100", "101", "102"]
    assert result.known_ids == ["100"]
    assert result.new_ids == ["101", "102"]


def test_detect_english_status_flags_german_markers() -> None:
    english = detect_english_status("Application deadline and requirements")
    german = detect_english_status("Bewerbungsfrist und Anforderungen")

    assert english["is_english"] is True
    assert german["is_english"] is False
