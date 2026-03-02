"""Ingestion step: Scrape job postings and ingest them into the pipeline.

This step wraps the existing scraper modules (scrape_single_url, fetch_listing,
generate_populated_tracker) into the step protocol. The scraper logic remains
unchanged — this is purely an orchestration layer using JobState for path management.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from src.scraper.fetch_listing import crawl_listing
from src.scraper.generate_populated_tracker import regenerate_job_markdown
from src.scraper.scrape_single_url import run_for_url
from src.steps import StepResult
from src.utils.state import JobState, PIPELINE_ROOT


def run(
    state: JobState,
    *,
    force: bool = False,
    url: str | None = None,
    strict_english: bool = True,
) -> StepResult:
    """
    Ingest a job posting.

    If url is provided, scrapes it fresh. Otherwise, if raw/raw.html exists,
    regenerates job.md and extracted.json from it. If neither, returns error.

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist (ingestion, not STEP_OUTPUTS)
        url: Optional URL to scrape. If provided, fresh scrape occurs.
        strict_english: Fail if extracted content is not confidently English

    Returns:
        StepResult with status, produced files, message
    """
    # Check if step already complete and not force
    if not force and state.step_complete("ingestion"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"Ingestion already complete for job {state.job_id}",
        )

    produced: list[str] = []

    # Case 1: URL provided — fresh scrape
    if url:
        try:
            result = run_for_url(
                url=url,
                source=state.source,
                pipeline_root=PIPELINE_ROOT,
                strict_english=strict_english,
            )
            # Map returned paths to relative paths within job_dir
            for rel_artifact in state.STEP_OUTPUTS["ingestion"]:
                full_path = state.artifact_path(rel_artifact)
                if full_path.exists():
                    produced.append(rel_artifact)

            return StepResult(
                status="ok",
                produced=produced,
                comments_found=0,
                message=f"Scraped job {state.job_id} from URL: {url}",
            )
        except Exception as e:
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"Failed to scrape {state.job_id}: {e}",
            )

    # Case 2: No URL provided — try to regenerate from existing raw.html
    raw_html_path = state.artifact_path("raw/raw.html")
    if raw_html_path.exists():
        try:
            regenerate_job_markdown(state.job_dir)
            # Track all produced outputs
            for rel_artifact in state.STEP_OUTPUTS["ingestion"]:
                full_path = state.artifact_path(rel_artifact)
                if full_path.exists():
                    produced.append(rel_artifact)

            return StepResult(
                status="ok",
                produced=produced,
                comments_found=0,
                message=f"Regenerated ingestion artifacts for job {state.job_id}",
            )
        except Exception as e:
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"Failed to regenerate artifacts for {state.job_id}: {e}",
            )

    # Case 3: Neither URL nor raw.html — cannot proceed
    return StepResult(
        status="error",
        produced=[],
        comments_found=0,
        message=(
            f"Cannot ingest job {state.job_id}: no URL provided and "
            f"no raw/raw.html found. Use --url to scrape."
        ),
    )


def run_from_url(
    url: str,
    source: str = "tu_berlin",
    *,
    strict_english: bool = True,
) -> StepResult:
    """
    Ingest from a single URL.

    Extracts the job_id from the URL, creates JobState, and calls run().

    Args:
        url: Full URL to the job posting (e.g., https://www.jobs.tu-berlin.de/en/job-postings/201084)
        source: Source name for job organization (default: "tu_berlin")
        strict_english: Fail if extracted content is not confidently English

    Returns:
        StepResult with status, produced files, message

    Raises:
        ValueError: If job_id cannot be extracted from URL
    """
    # Extract job_id from URL
    match = re.search(r"/(\d+)(?:\?.*)?$", url.strip())
    if not match:
        return StepResult(
            status="error",
            produced=[],
            comments_found=0,
            message=f"Could not extract numeric job ID from URL: {url}",
        )

    job_id = match.group(1)

    # Create JobState and run ingestion
    try:
        state = JobState(job_id, source=source)
    except ValueError as e:
        return StepResult(
            status="error",
            produced=[],
            comments_found=0,
            message=f"Cannot ingest job {job_id}: {e}",
        )

    return run(state, url=url, strict_english=strict_english)


def run_from_listing(
    listing_url: str,
    source: str = "tu_berlin",
    *,
    strict_english: bool = True,
    delay: float = 0.5,
) -> list[StepResult]:
    """
    Crawl a listing page and ingest all new jobs.

    Fetches the listing page, extracts all job URLs, and calls run_from_url()
    for each new job (skipping already-ingested jobs).

    Args:
        listing_url: Full URL to a paginated listing page
        source: Source name for job organization (default: "tu_berlin")
        strict_english: Fail if any extracted content is not confidently English
        delay: Seconds to sleep between URL fetches (default: 0.5)

    Returns:
        List of StepResult, one per job found on the listing
    """
    results: list[StepResult] = []

    try:
        crawl_result = crawl_listing(
            listing_url=listing_url,
            source=source,
            pipeline_root=PIPELINE_ROOT,
            strict_english=strict_english,
            delay=delay,
        )

        # crawl_result has keys: "scraped", "skipped", "failed"
        # "scraped" contains job_ids that were successfully ingested

        for job_id in crawl_result.get("scraped", []):
            # Construct URL and call run_from_url
            job_url = _construct_job_url(listing_url, job_id)
            result = run_from_url(job_url, source=source, strict_english=strict_english)
            results.append(result)
            time.sleep(delay)

        # For already-known jobs (skipped)
        for job_id in crawl_result.get("skipped", []):
            results.append(
                StepResult(
                    status="skipped",
                    produced=[],
                    comments_found=0,
                    message=f"Job {job_id} already ingested",
                )
            )

        # For failed scrapes
        for job_id in crawl_result.get("failed", []):
            results.append(
                StepResult(
                    status="error",
                    produced=[],
                    comments_found=0,
                    message=f"Failed to scrape job {job_id}",
                )
            )

    except Exception as e:
        return [
            StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"Failed to crawl listing {listing_url}: {e}",
            )
        ]

    return results


def _construct_job_url(listing_url: str, job_id: str) -> str:
    """Construct a job URL from a listing URL and job_id.

    Extracts the base domain from the listing URL and builds the job URL.
    """
    from urllib.parse import urlparse

    parsed = urlparse(listing_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    return f"{base_domain}/en/job-postings/{job_id}"
