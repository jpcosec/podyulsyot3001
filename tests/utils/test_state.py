"""Tests for JobState class."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from src.utils.state import JobState, PIPELINE_ROOT


@pytest.fixture
def temp_pipeline(tmp_path):
    """Create a temporary pipeline root for testing."""
    # Create the directory structure: tmp_path/tu_berlin/
    source_root = tmp_path / "tu_berlin"
    source_root.mkdir(parents=True, exist_ok=True)

    # Monkey-patch PIPELINE_ROOT during test
    original_pipeline_root = PIPELINE_ROOT
    import src.utils.state

    src.utils.state.PIPELINE_ROOT = tmp_path
    yield tmp_path

    # Restore original
    src.utils.state.PIPELINE_ROOT = original_pipeline_root


@pytest.fixture
def job_with_extracted_json(temp_pipeline):
    """Create a job directory with extracted.json."""
    job_id = "201084"
    job_dir = temp_pipeline / "tu_berlin" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = job_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    extracted = {
        "status": "open",
        "deadline": "2026-03-06",
        "reference_number": "III-51/26",
        "university": "TU Berlin",
        "category": "Research Associate",
        "title": "Research Assistant in Bioprocess Engineering",
        "url": "https://www.jobs.tu-berlin.de/en/job-postings/201084",
    }
    with open(raw_dir / "extracted.json", "w") as f:
        json.dump(extracted, f)

    return job_id


class TestJobDirPathResolution:
    """Test path resolution for job directories."""

    def test_job_dir_path_resolution(self, temp_pipeline, job_with_extracted_json):
        """Verify job_dir property returns correct path."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        expected = temp_pipeline / "tu_berlin" / job_id
        assert state.job_dir == expected
        assert state.job_dir.exists()

    def test_artifact_path(self, temp_pipeline, job_with_extracted_json):
        """Verify artifact_path returns correct absolute path."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Test various relative paths
        assert state.artifact_path("raw/extracted.json") == (
            temp_pipeline / "tu_berlin" / job_id / "raw" / "extracted.json"
        )
        assert state.artifact_path("planning/match_proposal.md") == (
            temp_pipeline / "tu_berlin" / job_id / "planning" / "match_proposal.md"
        )
        assert state.artifact_path("output/cv.pdf") == (
            temp_pipeline / "tu_berlin" / job_id / "output" / "cv.pdf"
        )


class TestArtifactIO:
    """Test artifact reading and writing."""

    def test_read_artifact(self, temp_pipeline, job_with_extracted_json):
        """Test reading a text artifact."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Write a test artifact first
        content = "Test content\nLine 2"
        state.write_artifact("planning/test.md", content)

        # Read it back
        result = state.read_artifact("planning/test.md")
        assert result == content

    def test_write_artifact_creates_parents(self, temp_pipeline, job_with_extracted_json):
        """Verify write_artifact creates parent directories."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Write to a deep path
        path = state.write_artifact("a/b/c/d/test.txt", "content")

        assert path.exists()
        assert path.read_text() == "content"

    def test_read_json_artifact(self, temp_pipeline, job_with_extracted_json):
        """Test reading a JSON artifact."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        data = {"key": "value", "nested": {"field": 123}}
        state.write_json_artifact("planning/test.json", data)

        result = state.read_json_artifact("planning/test.json")
        assert result == data

    def test_write_json_artifact(self, temp_pipeline, job_with_extracted_json):
        """Test writing a JSON artifact."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        data = {"status": "ok", "count": 42}
        path = state.write_json_artifact("output/result.json", data)

        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == data


class TestMetadata:
    """Test metadata loading from extracted.json."""

    def test_metadata_from_extracted_json(self, temp_pipeline, job_with_extracted_json):
        """Verify metadata property loads from raw/extracted.json."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        metadata = state.metadata
        assert metadata["status"] == "open"
        assert metadata["deadline"] == "2026-03-06"
        assert metadata["reference_number"] == "III-51/26"

    def test_metadata_missing_file(self, temp_pipeline):
        """Verify metadata returns empty dict if file doesn't exist."""
        job_id = "201999"
        job_dir = temp_pipeline / "tu_berlin" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        state = JobState(job_id, source="tu_berlin")
        assert state.metadata == {}

    def test_metadata_cached(self, temp_pipeline, job_with_extracted_json):
        """Verify metadata is cached after first load."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # First access
        first = state.metadata
        # Second access should return the same object
        second = state.metadata
        assert first is second

    def test_deadline_parsing_iso_date(self, temp_pipeline):
        """Verify deadline property parses ISO 8601 date."""
        job_id = "201100"
        job_dir = temp_pipeline / "tu_berlin" / job_id
        raw_dir = job_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        extracted = {"deadline": "2026-03-06"}
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump(extracted, f)

        state = JobState(job_id, source="tu_berlin")
        assert state.deadline == date(2026, 3, 6)

    def test_deadline_parsing_iso_datetime(self, temp_pipeline):
        """Verify deadline property parses ISO 8601 datetime."""
        job_id = "201101"
        job_dir = temp_pipeline / "tu_berlin" / job_id
        raw_dir = job_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        extracted = {"deadline": "2026-03-06T14:30:00Z"}
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump(extracted, f)

        state = JobState(job_id, source="tu_berlin")
        assert state.deadline == date(2026, 3, 6)

    def test_deadline_missing(self, temp_pipeline):
        """Verify deadline returns None if missing."""
        job_id = "201102"
        job_dir = temp_pipeline / "tu_berlin" / job_id
        raw_dir = job_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        extracted = {"status": "open"}
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump(extracted, f)

        state = JobState(job_id, source="tu_berlin")
        assert state.deadline is None

    def test_deadline_invalid(self, temp_pipeline):
        """Verify deadline returns None for invalid date."""
        job_id = "201103"
        job_dir = temp_pipeline / "tu_berlin" / job_id
        raw_dir = job_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        extracted = {"deadline": "not-a-date"}
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump(extracted, f)

        state = JobState(job_id, source="tu_berlin")
        assert state.deadline is None


class TestStepTracking:
    """Test step completion and tracking."""

    def test_step_complete_all_outputs_exist(self, temp_pipeline, job_with_extracted_json):
        """Verify step_complete returns True when all outputs exist."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Create all ingestion outputs
        for output in JobState.STEP_OUTPUTS["ingestion"]:
            state.write_artifact(output, "dummy content")

        assert state.step_complete("ingestion") is True

    def test_step_complete_missing_output(self, temp_pipeline, job_with_extracted_json):
        """Verify step_complete returns False when any output is missing."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        outputs = JobState.STEP_OUTPUTS["ingestion"]
        # Create all but the first output
        for output in outputs[1:]:
            state.write_artifact(output, "dummy")

        assert state.step_complete("ingestion") is False

    def test_step_complete_invalid_step(self, temp_pipeline, job_with_extracted_json):
        """Verify step_complete returns False for invalid step name."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        assert state.step_complete("nonexistent_step") is False

    def test_pending_steps(self, temp_pipeline, job_with_extracted_json):
        """Verify pending_steps returns only incomplete steps."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Initially, all steps are pending
        pending = state.pending_steps()
        assert len(pending) == len(JobState.STEP_ORDER)
        assert pending == JobState.STEP_ORDER

        # Complete ingestion
        for output in JobState.STEP_OUTPUTS["ingestion"]:
            state.write_artifact(output, "dummy")

        pending = state.pending_steps()
        assert "ingestion" not in pending
        assert "matching" in pending

    def test_completed_steps(self, temp_pipeline, job_with_extracted_json):
        """Verify completed_steps returns only complete steps."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Initially, no steps are complete
        assert state.completed_steps() == []

        # Complete ingestion
        for output in JobState.STEP_OUTPUTS["ingestion"]:
            state.write_artifact(output, "dummy")

        completed = state.completed_steps()
        assert completed == ["ingestion"]

    def test_next_step(self, temp_pipeline, job_with_extracted_json):
        """Verify next_step returns first incomplete step."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Initially, first step is next
        assert state.next_step() == "ingestion"

        # Complete ingestion
        for output in JobState.STEP_OUTPUTS["ingestion"]:
            state.write_artifact(output, "dummy")

        # Now matching is next
        assert state.next_step() == "matching"

    def test_next_step_all_complete(self, temp_pipeline, job_with_extracted_json):
        """Verify next_step returns None when all steps are complete."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Complete all steps
        for step in JobState.STEP_ORDER:
            for output in JobState.STEP_OUTPUTS[step]:
                state.write_artifact(output, "dummy")

        assert state.next_step() is None


class TestArchive:
    """Test archive detection and operations."""

    def test_is_archived_false_for_open_job(self, temp_pipeline, job_with_extracted_json):
        """Verify is_archived returns False for non-archived job."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        assert state.is_archived is False

    def test_is_archived_true_for_archived_job(self, temp_pipeline):
        """Verify is_archived returns True for archived job."""
        job_id = "201200"
        archive_dir = temp_pipeline / "tu_berlin" / "archive" / job_id
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create a bare extracted.json so constructor doesn't fail
        raw_dir = archive_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump({}, f)

        # Constructor should raise for archived jobs
        with pytest.raises(ValueError, match="archived and cannot be operated on"):
            JobState(job_id, source="tu_berlin")

    def test_archive_refuses_operation_on_archived_job(self, temp_pipeline):
        """Verify constructor raises ValueError for archived jobs."""
        job_id = "201300"
        archive_dir = temp_pipeline / "tu_berlin" / "archive" / job_id
        archive_dir.mkdir(parents=True, exist_ok=True)

        raw_dir = archive_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump({}, f)

        with pytest.raises(ValueError):
            JobState(job_id, source="tu_berlin")

    def test_archive_moves_job_dir(self, temp_pipeline, job_with_extracted_json):
        """Verify archive() moves job to archive subdirectory."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        original_path = state.job_dir
        assert original_path.exists()

        state.archive()

        archive_path = temp_pipeline / "tu_berlin" / "archive" / job_id
        assert not original_path.exists()
        assert archive_path.exists()

    def test_archive_idempotent_on_empty(self, temp_pipeline, job_with_extracted_json):
        """Verify archive works even if archive dir doesn't exist."""
        job_id = job_with_extracted_json
        state = JobState(job_id, source="tu_berlin")

        # Archive should create the archive directory if needed
        state.archive()

        archive_path = temp_pipeline / "tu_berlin" / "archive" / job_id
        assert archive_path.exists()


class TestListOpenJobs:
    """Test listing and querying jobs."""

    def test_list_open_jobs_empty_source(self, temp_pipeline):
        """Verify list_open_jobs returns empty list for nonexistent source."""
        result = JobState.list_open_jobs(source="nonexistent")
        assert result == []

    def test_list_open_jobs(self, temp_pipeline):
        """Verify list_open_jobs returns all non-archived jobs."""
        # Create three jobs
        for job_id in ["201084", "201085", "201086"]:
            job_dir = temp_pipeline / "tu_berlin" / job_id
            raw_dir = job_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            with open(raw_dir / "extracted.json", "w") as f:
                json.dump({}, f)

        # Create one archived job
        archive_dir = temp_pipeline / "tu_berlin" / "archive" / "201087"
        raw_dir = archive_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump({}, f)

        result = JobState.list_open_jobs(source="tu_berlin")
        assert len(result) == 3
        assert all(not job.is_archived for job in result)
        assert [job.job_id for job in result] == ["201084", "201085", "201086"]

    def test_list_open_jobs_sorted(self, temp_pipeline):
        """Verify list_open_jobs returns sorted results."""
        # Create jobs in random order
        for job_id in ["201086", "201084", "201085"]:
            job_dir = temp_pipeline / "tu_berlin" / job_id
            raw_dir = job_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            with open(raw_dir / "extracted.json", "w") as f:
                json.dump({}, f)

        result = JobState.list_open_jobs(source="tu_berlin")
        assert [job.job_id for job in result] == ["201084", "201085", "201086"]

    def test_list_expiring(self, temp_pipeline):
        """Verify list_expiring filters by deadline proximity."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        two_weeks = today + timedelta(days=14)

        jobs_data = [
            ("201084", tomorrow),
            ("201085", next_week),
            ("201086", two_weeks),
        ]

        for job_id, deadline in jobs_data:
            job_dir = temp_pipeline / "tu_berlin" / job_id
            raw_dir = job_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            with open(raw_dir / "extracted.json", "w") as f:
                json.dump({"deadline": deadline.isoformat()}, f)

        # List jobs expiring within 7 days
        result = JobState.list_expiring(days=7, source="tu_berlin")
        assert len(result) == 2
        assert [job.job_id for job in result] == ["201084", "201085"]

    def test_list_expired(self, temp_pipeline):
        """Verify list_expired filters past-deadline jobs."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        tomorrow = today + timedelta(days=1)

        jobs_data = [
            ("201084", week_ago),
            ("201085", yesterday),
            ("201086", tomorrow),
        ]

        for job_id, deadline in jobs_data:
            job_dir = temp_pipeline / "tu_berlin" / job_id
            raw_dir = job_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            with open(raw_dir / "extracted.json", "w") as f:
                json.dump({"deadline": deadline.isoformat()}, f)

        result = JobState.list_expired(source="tu_berlin")
        assert len(result) == 2
        assert [job.job_id for job in result] == ["201084", "201085"]

    def test_list_by_keyword(self, temp_pipeline):
        """Verify list_by_keyword filters by matching keywords."""
        # Create jobs with and without keywords
        job_with_keywords = "201084"
        job_without_keywords = "201085"

        for job_id in [job_with_keywords, job_without_keywords]:
            job_dir = temp_pipeline / "tu_berlin" / job_id
            raw_dir = job_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            with open(raw_dir / "extracted.json", "w") as f:
                json.dump({}, f)

        # Add keywords to first job
        job1_state = JobState(job_with_keywords, source="tu_berlin")
        keywords_data = {"keywords": ["bioprocess", "fermentation", "python"]}
        job1_state.write_json_artifact("planning/keywords.json", keywords_data)

        # Search for keyword
        result = JobState.list_by_keyword("bioprocess", source="tu_berlin")
        assert len(result) == 1
        assert result[0].job_id == job_with_keywords

    def test_list_by_keyword_case_insensitive(self, temp_pipeline):
        """Verify list_by_keyword search is case-insensitive."""
        job_id = "201084"
        job_dir = temp_pipeline / "tu_berlin" / job_id
        raw_dir = job_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        with open(raw_dir / "extracted.json", "w") as f:
            json.dump({}, f)

        state = JobState(job_id, source="tu_berlin")
        state.write_json_artifact("planning/keywords.json", {"keywords": ["BioProcess"]})

        # Search with different case
        result = JobState.list_by_keyword("bioprocess", source="tu_berlin")
        assert len(result) == 1
        assert result[0].job_id == job_id

    def test_list_by_keyword_skips_missing_file(self, temp_pipeline):
        """Verify list_by_keyword skips jobs without keywords.json."""
        # Create two jobs, only first has keywords
        for job_id in ["201084", "201085"]:
            job_dir = temp_pipeline / "tu_berlin" / job_id
            raw_dir = job_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            with open(raw_dir / "extracted.json", "w") as f:
                json.dump({}, f)

        # Add keywords to first job only
        state1 = JobState("201084", source="tu_berlin")
        state1.write_json_artifact(
            "planning/keywords.json", {"keywords": ["bioprocess"]}
        )

        result = JobState.list_by_keyword("bioprocess", source="tu_berlin")
        assert len(result) == 1
        assert result[0].job_id == "201084"
