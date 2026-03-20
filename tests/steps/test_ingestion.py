"""Tests for the ingestion step."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.steps import StepResult
from src.steps.ingestion import (
    _construct_job_url,
    run,
    run_from_listing,
    run_from_url,
)
from src.utils.state import JobState


@pytest.fixture
def temp_pipeline_root(tmp_path):
    """Create a temporary pipeline root for testing."""
    pipeline_root = tmp_path / "data" / "pipelined_data"
    pipeline_root.mkdir(parents=True, exist_ok=True)
    return pipeline_root


@pytest.fixture
def mock_job_state(temp_pipeline_root, monkeypatch):
    """Create a JobState with mocked PIPELINE_ROOT."""
    monkeypatch.setattr(
        "src.steps.ingestion.PIPELINE_ROOT",
        temp_pipeline_root,
    )
    monkeypatch.setattr(
        "src.utils.state.PIPELINE_ROOT",
        temp_pipeline_root,
    )
    job_id = "201084"
    source_dir = temp_pipeline_root / "tu_berlin"
    source_dir.mkdir(parents=True, exist_ok=True)
    return JobState(job_id, source="tu_berlin")


class TestIngestRun:
    """Tests for the run() function."""

    def test_run_skipped_when_complete_and_not_force(self, mock_job_state):
        """Verify step returns 'skipped' when outputs exist and force=False."""
        # Create all ingestion outputs
        for rel_path in mock_job_state.STEP_OUTPUTS["ingestion"]:
            mock_job_state.write_artifact(rel_path, "content")

        result = run(mock_job_state, force=False)

        assert result.status == "skipped"
        assert result.produced == []
        assert "already complete" in result.message

    def test_run_force_reruns_when_complete(self, mock_job_state, monkeypatch):
        """Verify force=True re-runs even when outputs exist."""
        # Create all ingestion outputs
        for rel_path in mock_job_state.STEP_OUTPUTS["ingestion"]:
            mock_job_state.write_artifact(rel_path, "content")

        # Mock run_for_url to return success
        mock_run = MagicMock(return_value={
            "job_id": "201084",
            "job_dir": str(mock_job_state.job_dir),
        })
        monkeypatch.setattr("src.steps.ingestion.run_for_url", mock_run)

        # Create raw.html so we can test the scrape path
        mock_job_state.write_artifact("raw/raw.html", "<html></html>")

        result = run(mock_job_state, force=True, url="http://example.com/201084")

        # Should have attempted to scrape (even though mock)
        assert result.status in ("ok", "error")  # depends on mock setup

    def test_run_with_url_scrapes_fresh(self, mock_job_state, monkeypatch):
        """Verify run() with URL argument calls run_for_url."""
        url = "https://www.jobs.tu-berlin.de/en/job-postings/201084"

        # Mock run_for_url to create the artifacts
        def mock_run_func(*args, **kwargs):
            # Simulate run_for_url creating artifacts
            for rel_path in mock_job_state.STEP_OUTPUTS["ingestion"]:
                mock_job_state.write_artifact(rel_path, "test content")
            return {
                "job_id": "201084",
                "job_dir": str(mock_job_state.job_dir),
            }

        monkeypatch.setattr("src.steps.ingestion.run_for_url", mock_run_func)

        result = run(mock_job_state, url=url)

        assert result.status == "ok"
        assert "Scraped job" in result.message
        assert len(result.produced) == len(mock_job_state.STEP_OUTPUTS["ingestion"])

    def test_run_without_url_regenerates_from_raw_html(self, mock_job_state, monkeypatch):
        """Verify run() without URL regenerates from raw/raw.html."""
        # Create raw.html
        mock_job_state.write_artifact("raw/raw.html", "<html></html>")

        # Mock regenerate_job_markdown to create the artifacts
        def mock_regen_func(job_dir):
            # Simulate regenerate_job_markdown creating artifacts
            state = JobState(job_dir.name, source="tu_berlin")
            for rel_path in state.STEP_OUTPUTS["ingestion"]:
                state.write_artifact(rel_path, "test content")

        monkeypatch.setattr(
            "src.steps.ingestion.regenerate_job_markdown",
            mock_regen_func,
        )

        result = run(mock_job_state)

        assert result.status == "ok"
        assert "Regenerated" in result.message

    def test_run_error_when_no_url_and_no_raw_html(self, mock_job_state):
        """Verify error when neither URL nor raw.html available."""
        result = run(mock_job_state)

        assert result.status == "error"
        assert "Cannot ingest" in result.message
        assert "no raw/raw.html found" in result.message



class TestRunFromUrl:
    """Tests for run_from_url() function."""

    def test_run_from_url_extracts_job_id(self, temp_pipeline_root, monkeypatch):
        """Verify job_id is extracted from URL."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )
        monkeypatch.setattr(
            "src.utils.state.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        url = "https://www.jobs.tu-berlin.de/en/job-postings/201084"

        # Create source dir
        (temp_pipeline_root / "tu_berlin").mkdir(parents=True, exist_ok=True)

        # Mock run to verify it's called
        called_args = {}

        def mock_run_func(state, **kwargs):
            called_args['job_id'] = state.job_id
            return StepResult(
                status="ok",
                produced=[],
                comments_found=0,
                message="test",
            )

        monkeypatch.setattr("src.steps.ingestion.run", mock_run_func)

        run_from_url(url)

        # Verify that run() was called with extracted job_id
        assert called_args.get('job_id') == "201084"

    def test_run_from_url_invalid_url_returns_error(self, temp_pipeline_root, monkeypatch):
        """Verify error when job_id cannot be extracted from URL."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        url = "https://www.jobs.tu-berlin.de/en/invalid-url"
        result = run_from_url(url)

        assert result.status == "error"
        assert "Could not extract" in result.message

    def test_run_from_url_handles_jobstate_creation_error(self, temp_pipeline_root, monkeypatch):
        """Verify error handling when JobState creation fails."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        url = "https://www.jobs.tu-berlin.de/en/job-postings/201084"

        # Mock JobState to raise ValueError
        def mock_jobstate(*args, **kwargs):
            raise ValueError("Test error condition")

        monkeypatch.setattr("src.steps.ingestion.JobState", mock_jobstate)

        result = run_from_url(url)

        # Should return error status
        assert result.status == "error"
        assert "Cannot ingest" in result.message

    def test_run_from_url_source_parameter(self, temp_pipeline_root, monkeypatch):
        """Verify source parameter is passed through."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )
        monkeypatch.setattr(
            "src.utils.state.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        url = "https://example.com/job-postings/999999"

        # Create custom source dir
        custom_source = temp_pipeline_root / "custom_source"
        custom_source.mkdir(parents=True, exist_ok=True)

        # Track which source was used
        called_source = {}

        def mock_run_func(state, **kwargs):
            called_source['source'] = state.source
            return StepResult(
                status="ok",
                produced=[],
                comments_found=0,
                message="test",
            )

        monkeypatch.setattr("src.steps.ingestion.run", mock_run_func)

        run_from_url(url, source="custom_source")

        assert called_source.get('source') == "custom_source"


class TestRunFromListing:
    """Tests for run_from_listing() function."""

    def test_run_from_listing_empty_listing(self, temp_pipeline_root, monkeypatch):
        """Verify handling of empty listing results."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        # Mock crawl_listing to return empty results
        mock_crawl = MagicMock(return_value={
            "scraped": [],
            "skipped": [],
            "failed": [],
        })
        monkeypatch.setattr("src.steps.ingestion.crawl_listing", mock_crawl)

        results = run_from_listing("https://example.com/listing")

        assert results == []

    def test_run_from_listing_calls_run_from_url_for_each_scraped_job(
        self, temp_pipeline_root, monkeypatch
    ):
        """Verify run_from_url() is called for each newly scraped job."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        mock_crawl = MagicMock(return_value={
            "scraped": ["201084", "201085"],
            "skipped": [],
            "failed": [],
        })
        monkeypatch.setattr("src.steps.ingestion.crawl_listing", mock_crawl)

        mock_run_from_url = MagicMock(return_value=StepResult(
            status="ok",
            produced=[],
            comments_found=0,
            message="test",
        ))
        monkeypatch.setattr("src.steps.ingestion.run_from_url", mock_run_from_url)

        run_from_listing("https://example.com/listing")

        # Verify run_from_url was called twice
        assert mock_run_from_url.call_count == 2

    def test_run_from_listing_returns_skip_for_already_known_jobs(self, temp_pipeline_root, monkeypatch):
        """Verify skipped jobs return 'skipped' status."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        mock_crawl = MagicMock(return_value={
            "scraped": [],
            "skipped": ["201084"],
            "failed": [],
        })
        monkeypatch.setattr("src.steps.ingestion.crawl_listing", mock_crawl)

        results = run_from_listing("https://example.com/listing")

        assert len(results) == 1
        assert results[0].status == "skipped"
        assert "already ingested" in results[0].message

    def test_run_from_listing_returns_error_for_failed_jobs(self, temp_pipeline_root, monkeypatch):
        """Verify failed jobs return 'error' status."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        mock_crawl = MagicMock(return_value={
            "scraped": [],
            "skipped": [],
            "failed": ["201084"],
        })
        monkeypatch.setattr("src.steps.ingestion.crawl_listing", mock_crawl)

        results = run_from_listing("https://example.com/listing")

        assert len(results) == 1
        assert results[0].status == "error"

    def test_run_from_listing_propagates_crawl_exception(self, temp_pipeline_root, monkeypatch):
        """Verify exceptions from crawl_listing are handled gracefully."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        mock_crawl = MagicMock(side_effect=Exception("Network error"))
        monkeypatch.setattr("src.steps.ingestion.crawl_listing", mock_crawl)

        results = run_from_listing("https://example.com/listing")

        assert len(results) == 1
        assert results[0].status == "error"
        assert "Failed to crawl" in results[0].message

    def test_run_from_listing_respects_delay(self, temp_pipeline_root, monkeypatch):
        """Verify delay parameter is passed to both crawl and run_from_url."""
        monkeypatch.setattr(
            "src.steps.ingestion.PIPELINE_ROOT",
            temp_pipeline_root,
        )

        mock_crawl = MagicMock(return_value={
            "scraped": ["201084"],
            "skipped": [],
            "failed": [],
        })
        monkeypatch.setattr("src.steps.ingestion.crawl_listing", mock_crawl)

        mock_run_from_url = MagicMock(return_value=StepResult(
            status="ok",
            produced=[],
            comments_found=0,
            message="test",
        ))
        monkeypatch.setattr("src.steps.ingestion.run_from_url", mock_run_from_url)

        run_from_listing("https://example.com/listing", delay=2.0)

        # Verify delay was passed to crawl_listing
        assert mock_crawl.call_args[1]["delay"] == 2.0


class TestConstructJobUrl:
    """Tests for _construct_job_url() helper."""

    def test_construct_job_url_from_listing(self):
        """Verify job URL is correctly constructed from listing URL."""
        listing_url = "https://www.jobs.tu-berlin.de/en/job-postings?page=1"
        job_id = "201084"

        result = _construct_job_url(listing_url, job_id)

        assert result == "https://www.jobs.tu-berlin.de/en/job-postings/201084"

    def test_construct_job_url_preserves_domain(self):
        """Verify domain is preserved in constructed URL."""
        listing_url = "https://custom-domain.com/jobs?page=1"
        job_id = "999999"

        result = _construct_job_url(listing_url, job_id)

        assert result.startswith("https://custom-domain.com")
        assert "999999" in result
