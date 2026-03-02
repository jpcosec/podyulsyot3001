"""Tests for the CV tailoring step."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.steps import StepResult
from src.steps.cv_tailoring import (
    run,
    _extract_comments_from_files,
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
        "src.utils.state.PIPELINE_ROOT",
        temp_pipeline_root,
    )
    job_id = "201084"
    source_dir = temp_pipeline_root / "tu_berlin"
    source_dir.mkdir(parents=True, exist_ok=True)
    return JobState(job_id, source="tu_berlin")


@pytest.fixture
def sample_job_md():
    """Sample job.md content."""
    return """# Research Assistant III-51/26, Bioprocess Engineering
reference_number: 201084
deadline: 2026-03-20
institution: TU Berlin
department: Department of Bioprocess Engineering

## Requirements

- [ ] PhD or advanced degree in bioprocess engineering or related field
- [ ] Experience with fermentation process control systems
- [ ] Python programming experience (3+ years)
- [ ] Experience with Airflow or similar workflow orchestration
- [ ] Excellent communication skills (German or English)

## Description

Research assistant position focusing on bioprocess optimization...
"""


@pytest.fixture
def sample_cvtailoring_pipeline_state():
    """Sample PipelineState from CVTailoringPipeline."""
    from src.models.pipeline_contract import (
        PipelineState,
        JobPosting,
        ProposedClaim,
    )

    return PipelineState(
        job=JobPosting(
            title="Research Assistant III-51/26, Bioprocess Engineering",
            reference_number="201084",
            deadline="2026-03-20",
            institution="TU Berlin",
            department="Department of Bioprocess Engineering",
            location="Berlin, Germany",
            contact_name="Dr. Smith",
            contact_email="smith@tu-berlin.de",
            requirements=[],
            themes=[],
            raw_text="",
        ),
        evidence_items=[],
        proposed_claims=[
            ProposedClaim(
                id="C1",
                target_section="experience",
                target_subsection="Work",
                claim_text="Designed and deployed Airflow pipelines for process control systems",
                based_on_evidence_ids=["E1"],
                status="approved",
            ),
            ProposedClaim(
                id="C2",
                target_section="skills",
                target_subsection="Programming",
                claim_text="5+ years Python development with scientific computing focus",
                based_on_evidence_ids=["E2"],
                status="approved",
            ),
            ProposedClaim(
                id="C3",
                target_section="education",
                target_subsection="Degrees",
                claim_text="MSc in Chemical Engineering with process engineering specialization",
                based_on_evidence_ids=["E3"],
                status="approved",
            ),
        ],
        mapping=[],
        render={},
    )


class TestCVTailoringRun:
    """Tests for the run() function."""

    def test_run_skipped_when_complete_and_not_force(self, mock_job_state):
        """Verify step returns 'skipped' when outputs exist and force=False."""
        # Create CV tailoring outputs
        for rel_path in mock_job_state.STEP_OUTPUTS["cv_tailoring"]:
            mock_job_state.write_artifact(rel_path, "content")

        result = run(mock_job_state, force=False)

        assert result.status == "skipped"
        assert result.produced == []
        assert "already complete" in result.message

    def test_run_error_when_job_md_missing(self, mock_job_state):
        """Verify run() returns error when job.md doesn't exist."""
        result = run(mock_job_state)

        assert result.status == "error"
        assert "job.md not found" in result.message

    def test_run_produces_tailoring_and_to_render(
        self, mock_job_state, sample_job_md, sample_cvtailoring_pipeline_state, monkeypatch
    ):
        """Verify run() produces planning/cv_tailoring.md and cv/to_render.md."""
        # Create job.md
        mock_job_state.write_artifact("job.md", sample_job_md)

        # Mock CVTailoringPipeline.execute to return sample state
        def mock_execute(self, job_id, source="tu_berlin"):
            # Simulate what the pipeline does: write tailoring.md
            tailoring_md = f"""# CV Tailoring Brief

- Job: {sample_cvtailoring_pipeline_state.job.title}
- Reference: {sample_cvtailoring_pipeline_state.job.reference_number}
- Approved claims: {len([c for c in sample_cvtailoring_pipeline_state.proposed_claims if c.status == 'approved'])}

## Approved Claims

- [Experience - Work] Designed and deployed Airflow pipelines for process control systems
- [Skills - Programming] 5+ years Python development with scientific computing focus
- [Education - Degrees] MSc in Chemical Engineering with process engineering specialization
"""
            tailoring_path = mock_job_state.artifact_path("planning/cv_tailoring.md")
            tailoring_path.parent.mkdir(parents=True, exist_ok=True)
            tailoring_path.write_text(tailoring_md, encoding="utf-8")

            return sample_cvtailoring_pipeline_state

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            mock_execute,
        )

        # Mock build_to_render_markdown
        def mock_build_markdown(model):
            return """# John Doe
Senior Research Engineer

## CONTACT
Phone: +49-123-456789
Email: john@example.com
Address: Berlin, Germany

## SUMMARY
Experienced engineer with focus on bioprocess optimization...

## EDUCATION
2020 - 2022
MSc Chemical Engineering - TU Berlin, Berlin
Specialization: Process Engineering

## WORK EXPERIENCE
### 2022 - Senior Research Engineer - TU Berlin - Berlin
Present
- Designed and deployed Airflow pipelines for process control systems
- Led optimization of fermentation processes

## TECHNICAL SKILLS
* Programming
Python, Rust, Go
* Process Control
Fermentation, SCADA, PLC

## LANGUAGES
* English: Fluent (C1)
* German: Fluent (C1)
"""

        monkeypatch.setattr(
            "src.cv_generator.__main__.build_to_render_markdown",
            mock_build_markdown,
        )

        result = run(mock_job_state)

        assert result.status == "ok"
        assert "planning/cv_tailoring.md" in result.produced
        assert "cv/to_render.md" in result.produced

        # Verify both files were written
        tailoring_content = mock_job_state.read_artifact("planning/cv_tailoring.md")
        assert "CV Tailoring Brief" in tailoring_content
        assert "Research Assistant III-51/26" in tailoring_content
        assert "Approved claims: 3" in tailoring_content

        to_render_content = mock_job_state.read_artifact("cv/to_render.md")
        assert "John Doe" in to_render_content
        assert "EDUCATION" in to_render_content
        assert "WORK EXPERIENCE" in to_render_content

    def test_run_reads_comments_from_previous_output(
        self, mock_job_state, sample_job_md, sample_cvtailoring_pipeline_state, monkeypatch
    ):
        """Verify run() reads comments from its own output and input files."""
        # Create job.md with a comment
        job_md_with_comment = sample_job_md + "\n<!-- Check if fermentation background is sufficient -->"
        mock_job_state.write_artifact("job.md", job_md_with_comment)

        # Create previous tailoring output with a comment
        tailoring_with_comment = """# CV Tailoring Brief

<!-- Need to emphasize process control experience more -->

- Job: Test Job
- Approved claims: 2

## Approved Claims

- [Experience] Claim 1
- [Skills] Claim 2
"""
        mock_job_state.write_artifact("planning/cv_tailoring.md", tailoring_with_comment)

        def mock_execute(self, job_id, source="tu_berlin"):
            tailoring_path = mock_job_state.artifact_path("planning/cv_tailoring.md")
            return sample_cvtailoring_pipeline_state

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            mock_execute,
        )

        def mock_build_markdown(model):
            return "# John Doe\n## EDUCATION"

        monkeypatch.setattr(
            "src.cv_generator.__main__.build_to_render_markdown",
            mock_build_markdown,
        )

        result = run(mock_job_state, force=True)

        assert result.status == "ok"
        # Should have found at least 1 comment (from either job.md or previous tailoring)
        assert result.comments_found >= 1

    def test_run_creates_to_render_if_missing(
        self, mock_job_state, sample_job_md, sample_cvtailoring_pipeline_state, monkeypatch
    ):
        """Verify run() creates cv/to_render.md even if pipeline doesn't."""
        mock_job_state.write_artifact("job.md", sample_job_md)

        # Mock pipeline that doesn't create to_render.md
        def mock_execute(self, job_id, source="tu_berlin"):
            tailoring_md = "# CV Tailoring Brief\n- Job: Test\n- Approved claims: 0"
            tailoring_path = mock_job_state.artifact_path("planning/cv_tailoring.md")
            tailoring_path.parent.mkdir(parents=True, exist_ok=True)
            tailoring_path.write_text(tailoring_md, encoding="utf-8")
            return sample_cvtailoring_pipeline_state

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            mock_execute,
        )

        def mock_build_markdown(model):
            return "# John Doe\n## SUMMARY\nTest summary"

        monkeypatch.setattr(
            "src.cv_generator.__main__.build_to_render_markdown",
            mock_build_markdown,
        )

        result = run(mock_job_state)

        assert result.status == "ok"
        assert "cv/to_render.md" in result.produced

        to_render_content = mock_job_state.read_artifact("cv/to_render.md")
        assert "John Doe" in to_render_content

    def test_run_error_when_pipeline_fails(self, mock_job_state, sample_job_md, monkeypatch):
        """Verify run() returns error when pipeline fails."""
        mock_job_state.write_artifact("job.md", sample_job_md)

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            MagicMock(side_effect=Exception("Pipeline error")),
        )

        result = run(mock_job_state)

        assert result.status == "error"
        assert "Failed" in result.message

    def test_run_language_parameter_ignored(
        self, mock_job_state, sample_job_md, sample_cvtailoring_pipeline_state, monkeypatch
    ):
        """Verify language parameter is accepted but doesn't break execution."""
        mock_job_state.write_artifact("job.md", sample_job_md)

        def mock_execute(self, job_id, source="tu_berlin"):
            tailoring_path = mock_job_state.artifact_path("planning/cv_tailoring.md")
            tailoring_path.parent.mkdir(parents=True, exist_ok=True)
            tailoring_path.write_text("# CV Tailoring\n", encoding="utf-8")
            return sample_cvtailoring_pipeline_state

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            mock_execute,
        )

        def mock_build_markdown(model):
            return "# John Doe"

        monkeypatch.setattr(
            "src.cv_generator.__main__.build_to_render_markdown",
            mock_build_markdown,
        )

        # Should accept language parameter without error
        result = run(mock_job_state, language="german")

        assert result.status == "ok"

    def test_run_to_render_structure(
        self, mock_job_state, sample_job_md, sample_cvtailoring_pipeline_state, monkeypatch
    ):
        """Verify to_render.md has correct structure matching ATS requirements."""
        mock_job_state.write_artifact("job.md", sample_job_md)

        def mock_execute(self, job_id, source="tu_berlin"):
            tailoring_path = mock_job_state.artifact_path("planning/cv_tailoring.md")
            tailoring_path.parent.mkdir(parents=True, exist_ok=True)
            tailoring_path.write_text("# CV Tailoring", encoding="utf-8")
            return sample_cvtailoring_pipeline_state

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            mock_execute,
        )

        def mock_build_markdown(model):
            # Returns markdown matching build_to_render_markdown structure
            return """# John Doe
Senior Research Engineer

## CONTACT
Phone: +49-123-456789
Email: john@example.com
Address: Berlin, Germany

## SUMMARY
Experienced engineer with focus on bioprocess optimization.

## EDUCATION
2020 - 2022
MSc Chemical Engineering - TU Berlin, Berlin

## WORK EXPERIENCE
### 2022 - Senior Research Engineer - TU Berlin - Berlin
Present
- Designed Airflow pipelines
- Optimized processes

## PUBLICATIONS
2024 - Advanced Bioprocess Control

## LANGUAGES
* English: Fluent

## TECHNICAL SKILLS
* Programming
Python, Rust
"""

        monkeypatch.setattr(
            "src.cv_generator.__main__.build_to_render_markdown",
            mock_build_markdown,
        )

        result = run(mock_job_state)

        assert result.status == "ok"

        to_render_content = mock_job_state.read_artifact("cv/to_render.md")

        # Verify sections are in order for ATS parity
        sections = ["# John Doe", "## CONTACT", "## SUMMARY", "## EDUCATION", "## WORK EXPERIENCE", "## LANGUAGES"]
        positions = [to_render_content.find(s) for s in sections]
        assert all(p != -1 for p in positions), "All sections should be present"
        assert positions == sorted(positions), "Sections should be in correct order"


class TestCommentExtraction:
    """Tests for _extract_comments_from_files()."""

    def test_extract_comments_from_multiple_files(self):
        """Verify comment extraction from multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            job_dir = tmpdir_path / "job"
            job_dir.mkdir()

            file1 = tmpdir_path / "file1.md"
            file1.write_text("Content\n<!-- Comment 1 -->", encoding="utf-8")

            file2 = tmpdir_path / "file2.md"
            file2.write_text("More content\n<!-- Comment 2 -->", encoding="utf-8")

            file3 = tmpdir_path / "nonexistent.md"

            comments = _extract_comments_from_files(
                [file1, file2, file3], job_dir
            )

            assert len(comments) >= 2

    def test_extract_comments_from_nonexistent_files(self):
        """Verify graceful handling of nonexistent files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            job_dir = tmpdir_path / "job"

            file1 = tmpdir_path / "missing1.md"
            file2 = tmpdir_path / "missing2.md"

            # Should not raise error
            comments = _extract_comments_from_files([file1, file2], job_dir)

            assert comments == []

    def test_extract_comments_empty_list(self):
        """Verify handling of empty file list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            job_dir = Path(tmpdir)

            comments = _extract_comments_from_files([], job_dir)

            assert comments == []


class TestCVTailoringIntegration:
    """Integration tests for CV tailoring workflow."""

    def test_full_workflow_from_job_md_to_to_render(
        self, mock_job_state, sample_job_md, sample_cvtailoring_pipeline_state, monkeypatch
    ):
        """Verify full workflow from job.md to to_render.md output."""
        mock_job_state.write_artifact("job.md", sample_job_md)

        def mock_execute(self, job_id, source="tu_berlin"):
            tailoring_path = mock_job_state.artifact_path("planning/cv_tailoring.md")
            tailoring_path.parent.mkdir(parents=True, exist_ok=True)
            content = f"""# CV Tailoring Brief

- Job: Research Assistant III-51/26
- Reference: 201084
- Approved claims: {len([c for c in sample_cvtailoring_pipeline_state.proposed_claims if c.status == 'approved'])}

## Approved Claims

- [Experience] Designed Airflow pipelines for process control
- [Skills] 5+ years Python development
- [Education] MSc Chemical Engineering
"""
            tailoring_path.write_text(content, encoding="utf-8")
            return sample_cvtailoring_pipeline_state

        monkeypatch.setattr(
            "src.steps.cv_tailoring.CVTailoringPipeline.execute",
            mock_execute,
        )

        def mock_build_markdown(model):
            return """# John Doe
Senior Research Engineer

## CONTACT
Phone: +49-30-12345678
Email: john.doe@example.com
Address: Berlin, Germany

## SUMMARY
Experienced bioprocess engineer with focus on automation and control systems.

## EDUCATION
2020 - 2022
MSc in Chemical Engineering - TU Berlin, Berlin
Specialization: Process Engineering

## WORK EXPERIENCE
### 2022 - Present - Senior Research Engineer - TU Berlin - Berlin
- Designed and deployed Airflow pipelines for automated process control
- Optimized fermentation batch processes reducing cycle time by 15%
- Implemented SCADA integration for real-time monitoring

## PUBLICATIONS
2024 - Bioprocess Optimization through Automated Control Systems - Journal of Biotechnology

## LANGUAGES
* English: Native / Bilingual Proficiency (C2)
* German: Fluent (C1)

## TECHNICAL SKILLS
* Programming Languages
Python, Rust, Go, Bash
* Process Control
Fermentation, SCADA, PLC Control, Automation
"""

        monkeypatch.setattr(
            "src.cv_generator.__main__.build_to_render_markdown",
            mock_build_markdown,
        )

        result = run(mock_job_state)

        assert result.status == "ok"
        assert result.produced == ["planning/cv_tailoring.md", "cv/to_render.md"]
        assert result.message.startswith("Tailored CV content")

        # Verify artifacts
        tailoring = mock_job_state.read_artifact("planning/cv_tailoring.md")
        assert "Approved claims: 3" in tailoring
        assert "Research Assistant" in tailoring

        to_render = mock_job_state.read_artifact("cv/to_render.md")
        assert "John Doe" in to_render
        assert "EDUCATION" in to_render
        assert "MSc in Chemical Engineering" in to_render
        assert "Airflow pipelines" in to_render
