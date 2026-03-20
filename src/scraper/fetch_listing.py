from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.scraper.scrape_single_url import download_html, run_for_url


JOB_LINK_RE = re.compile(r"/job-postings/(\d+)(?:[/?#]|$)")
BASE_DOMAIN = "https://www.jobs.tu-berlin.de"


def extract_job_urls_from_html(html: str) -> set[str]:
    """Extract numeric TU Berlin job IDs from listing page links."""
    soup = BeautifulSoup(html, "html.parser")
    job_ids: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        match = JOB_LINK_RE.search(anchor["href"])
        if match:
            job_ids.add(match.group(1))
    return job_ids


def collect_known_job_ids(pipeline_root: Path, source: str) -> set[str]:
    """Collect known job IDs from active and archive folders."""
    known: set[str] = set()
    source_dir = pipeline_root / source
    for scan_dir in (source_dir, source_dir / "archive"):
        if not scan_dir.is_dir():
            continue
        for child in scan_dir.iterdir():
            if child.is_dir() and child.name.isdigit():
                known.add(child.name)
    return known


def build_page_url(base_url: str, page: int) -> str:
    """Build a listing URL with a deterministic page query parameter."""
    if re.search(r"([?&])page=\d+", base_url):
        return re.sub(r"([?&])page=\d+", rf"\1page={page}", base_url, count=1)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page}"


def _resolve_job_base_domain(listing_url: str) -> str:
    parsed = urlparse(listing_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return BASE_DOMAIN


def crawl_listing(
    listing_url: str,
    source: str = "tu_berlin",
    pipeline_root: Path | None = None,
    delay: float = 0.5,
    max_pages: int = 100,
) -> dict[str, list[str]]:
    """Crawl a paginated listing URL and scrape only new jobs."""
    if pipeline_root is None:
        pipeline_root = Path("data/pipelined_data").resolve()

    known_ids = collect_known_job_ids(pipeline_root, source)
    discovered_ids: set[str] = set()

    previous_page_ids: set[str] | None = None
    page = 1
    while page <= max_pages:
        page_url = build_page_url(listing_url, page)
        try:
            html = download_html(page_url)
        except Exception as exc:
            print(f"[warn] failed to fetch page {page}: {exc}")
            break

        page_ids = extract_job_urls_from_html(html)
        if not page_ids:
            break
        if previous_page_ids is not None and page_ids == previous_page_ids:
            break

        discovered_ids.update(page_ids)
        previous_page_ids = page_ids
        page += 1
        time.sleep(delay)

    new_ids = discovered_ids - known_ids
    print(
        "[listing] Found "
        + f"{len(discovered_ids)} jobs, {len(new_ids)} new, "
        + f"{len(discovered_ids) - len(new_ids)} already known"
    )

    scraped: list[str] = []
    skipped: list[str] = sorted(discovered_ids - new_ids)
    failed: list[str] = []
    base_domain = _resolve_job_base_domain(listing_url)

    for job_id in sorted(new_ids):
        job_url = f"{base_domain}/en/job-postings/{job_id}"
        try:
            run_for_url(
                url=job_url,
                source=source,
                pipeline_root=pipeline_root,
            )
            scraped.append(job_id)
            print(f"[scraped] {job_id}")
        except Exception as exc:
            failed.append(job_id)
            print(f"[failed] {job_id}: {exc}")
        time.sleep(delay)

    return {
        "scraped": scraped,
        "skipped": skipped,
        "failed": failed,
    }
