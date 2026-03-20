from __future__ import annotations

from src.core.scraping.strategies.stepstone import (
    extract_stepstone_detail,
    extract_stepstone_listing_urls,
    is_stepstone_detail_url,
    is_stepstone_listing_url,
)


def test_stepstone_url_classification() -> None:
    assert is_stepstone_listing_url("https://www.stepstone.de/jobs/in-berlin")
    assert is_stepstone_detail_url(
        "https://www.stepstone.de/stellenangebote--x--13722274-inline.html"
    )


def test_extract_stepstone_listing_urls_prefers_job_title_links() -> None:
    html = """
    <html><body>
      <article data-at="job-item">
        <a data-at="job-item-title" href="/stellenangebote--Role-A--111-inline.html">A</a>
      </article>
      <a href="/stellenangebote--Role-B--222-inline.html">B</a>
    </body></html>
    """
    urls = extract_stepstone_listing_urls(html, "https://www.stepstone.de/jobs")
    assert urls == ["https://www.stepstone.de/stellenangebote--Role-A--111-inline.html"]


def test_extract_stepstone_detail_payload() -> None:
    html = """
    <html><body>
      <h1 data-at='header-job-title'>Senior ML Engineer</h1>
      <a data-at='header-company-name'>YOC AG</a>
      <span data-at='header-location'>Berlin</span>
      <span data-at='header-job-type'>Vollzeit</span>
      <span data-at='header-timeago'>vor 1 Tag</span>
      <span data-at='header-salary'>70k - 90k</span>
      <div data-at='jobad-content'>Your tasks THE ROLE Build models</div>
      <button data-at='apply-button'>Ich bin interessiert</button>
    </body></html>
    """
    payload = extract_stepstone_detail(html)
    assert payload["title"] == "Senior ML Engineer"
    assert payload["company"] == "YOC AG"
    assert payload["location"] == "Berlin"
    assert payload["application"]["apply_button_text"] == "Ich bin interessiert"
    assert "Build models" in payload["raw_text"]
