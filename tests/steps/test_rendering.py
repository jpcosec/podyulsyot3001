"""Tests for the rendering step."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.steps import StepResult
from src.steps.rendering import run, template_test, validate_ats
from src.utils.state import JobState


@pytest.fixture
def mock_job_state(tmp_path):
    """Create a mock JobState with temporary directories."""
    state = Mock(spec=JobState)
    state.job_id = "test_job_201084"
    state.source = "tu_berlin"
    state.job_dir = tmp_path / "test_job_201084"
    state.job_dir.mkdir(parents=True, exist_ok=True)

    # Create required subdirectories
    (state.job_dir / "cv").mkdir(parents=True, exist_ok=True)
    (state.job_dir / "planning").mkdir(parents=True, exist_ok=True)
    (state.job_dir / "output").mkdir(parents=True, exist_ok=True)
    (state.job_dir / ".metadata").mkdir(parents=True, exist_ok=True)

    # Mock artifact_path to return paths in the temp dir
    def artifact_path_fn(rel_path: str) -> Path:
        return state.job_dir / rel_path

    state.artifact_path = artifact_path_fn

    # Mock step_complete
    state.step_complete = Mock(return_value=False)

    return state


def test_run_renders_cv_pdf(mock_job_state: Mock):
    """Verify that run() renders cv/to_render.md to output/cv.pdf."""
    # Create required to_render.md
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe\n\n## SUMMARY\n\nExperienced...", encoding="utf-8")

    with patch("src.steps.rendering._render_cv") as mock_render_cv:
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(mock_job_state, force=False)

    assert result.status == "ok"
    assert "output/cv.pdf" in result.produced
    assert mock_render_cv.called


def test_run_renders_motivation_pdf(mock_job_state: Mock):
    """Verify that run() can render motivation_letter.md to output/motivation_letter.pdf."""
    # Create required files
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe\n\n## SUMMARY", encoding="utf-8")

    motivation_path = mock_job_state.job_dir / "planning" / "motivation_letter.md"
    motivation_path.parent.mkdir(parents=True, exist_ok=True)
    motivation_path.write_text("# Dear Hiring Committee\n\nI am interested...", encoding="utf-8")

    with patch("src.steps.rendering._render_cv"):
        with patch("src.steps.rendering._render_motivation_letter"):
            with patch("src.steps.rendering.append_to_comment_log"):
                result = run(mock_job_state, force=False, targets=["cv", "motivation"])

    assert result.status == "ok"
    assert "output/cv.pdf" in result.produced
    assert "output/motivation_letter.pdf" in result.produced


def test_run_skips_when_complete(mock_job_state: Mock):
    """Verify that run() returns 'skipped' when rendering is already complete."""
    mock_job_state.step_complete.return_value = True

    result = run(mock_job_state, force=False)

    assert result.status == "skipped"
    assert result.produced == []
    assert "already complete" in result.message


def test_run_force_reruns(mock_job_state: Mock):
    """Verify that run() re-runs when force=True even if step is complete."""
    mock_job_state.step_complete.return_value = True

    # Create required to_render.md
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    with patch("src.steps.rendering._render_cv"):
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(mock_job_state, force=True)

    assert result.status == "ok"
    assert "output/cv.pdf" in result.produced


def test_run_requires_to_render_md(mock_job_state: Mock):
    """Verify that run() returns error when cv/to_render.md is missing."""
    # Don't create to_render.md
    result = run(mock_job_state, force=False)

    assert result.status == "error"
    assert "cv/to_render.md not found" in result.message


def test_run_passes_rendering_options(mock_job_state: Mock):
    """Verify that run() passes rendering options to _render_cv."""
    # Create required to_render.md
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    with patch("src.steps.rendering._render_cv") as mock_render_cv:
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(
                mock_job_state,
                force=False,
                via="latex",
                docx_template="harvard",
                language="german",
            )

    assert result.status == "ok"
    # Verify _render_cv was called with correct options
    call_kwargs = mock_render_cv.call_args[1]
    assert call_kwargs["via"] == "latex"
    assert call_kwargs["docx_template"] == "harvard"
    assert call_kwargs["language"] == "german"


def test_run_reads_comments(mock_job_state: Mock):
    """Verify that run() extracts and logs comments from rendered files."""
    # Create required to_render.md with comments
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe\n<!-- TODO: fix formatting -->\n", encoding="utf-8")

    with patch("src.steps.rendering._render_cv"):
        with patch("src.steps.rendering.append_to_comment_log") as mock_log:
            with patch("src.steps.rendering.extract_comments") as mock_extract:
                mock_extract.return_value = [Mock()] * 2  # Return 2 comments

                result = run(mock_job_state, force=False)

    assert result.status == "ok"
    assert result.comments_found == 2
    assert mock_log.called


def test_run_handles_docx_rendering(mock_job_state: Mock):
    """Verify that run() handles DOCX rendering via="docx"."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    with patch("src.steps.rendering._render_cv") as mock_render_cv:
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(mock_job_state, force=False, via="docx")

    assert result.status == "ok"
    call_kwargs = mock_render_cv.call_args[1]
    assert call_kwargs["via"] == "docx"


def test_run_handles_latex_rendering(mock_job_state: Mock):
    """Verify that run() handles LaTeX rendering via="latex"."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    with patch("src.steps.rendering._render_cv") as mock_render_cv:
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(mock_job_state, force=False, via="latex")

    assert result.status == "ok"
    call_kwargs = mock_render_cv.call_args[1]
    assert call_kwargs["via"] == "latex"


def test_run_skips_motivation_if_missing(mock_job_state: Mock):
    """Verify that run() skips motivation letter if file doesn't exist."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    with patch("src.steps.rendering._render_cv"):
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(
                mock_job_state, force=False, targets=["cv", "motivation"]
            )

    # Should succeed with only CV rendered
    assert result.status == "ok"
    assert "output/cv.pdf" in result.produced
    assert "output/motivation_letter.pdf" not in result.produced


def test_run_handles_rendering_exception(mock_job_state: Mock):
    """Verify that run() handles exceptions gracefully."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    with patch("src.steps.rendering._render_cv") as mock_render_cv:
        mock_render_cv.side_effect = RuntimeError("Rendering failed")
        with patch("src.steps.rendering.append_to_comment_log"):
            result = run(mock_job_state, force=False)

    assert result.status == "error"
    assert "Failed to render outputs" in result.message


# ── validate_ats tests ──


def test_validate_ats_produces_report(mock_job_state: Mock):
    """Verify that validate_ats() produces an ATS report."""
    # Create mock rendered CV (PDF)
    pdf_path = mock_job_state.job_dir / "cv" / "rendered" / "cv.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_text("Mock PDF content", encoding="utf-8")

    mock_config = Mock()
    mock_paths = {
        "pdf": pdf_path,
        "docx": mock_job_state.job_dir / "cv" / "rendered" / "cv.docx",
        "ats": mock_job_state.job_dir / "cv" / "ats" / "report.json",
    }

    with patch("src.steps.rendering.CVConfig.from_defaults", return_value=mock_config):
        with patch("src.cv_generator.__main__.resolve_output_paths", return_value=mock_paths):
            with patch("src.cv_generator.__main__.load_job_description", return_value="Job description"):
                with patch("src.render.pdf.extract_pdf_text", return_value="CV text"):
                    with patch("src.cv_generator.ats.run_ats_analysis") as mock_ats:
                        mock_ats.return_value = {
                            "status": "ok",
                            "code_score": 70,
                            "llm_score": 75,
                            "final_score": 72.5,
                        }
                        with patch("src.cv_generator.ats.write_ats_report") as mock_write:
                            result = validate_ats(
                                mock_job_state,
                                ats_target="pdf",
                                via="docx",
                            )

    assert result["status"] == "ok"
    assert "final_score" in result
    assert result["ats_target"] == "pdf"


def test_validate_ats_handles_missing_pdf(mock_job_state: Mock):
    """Verify that validate_ats() raises error if PDF not found."""
    mock_config = Mock()
    mock_paths = {
        "pdf": mock_job_state.job_dir / "cv" / "rendered" / "nonexistent.pdf",
        "docx": mock_job_state.job_dir / "cv" / "rendered" / "cv.docx",
        "ats": mock_job_state.job_dir / "cv" / "ats" / "report.json",
    }

    with patch("src.steps.rendering.CVConfig.from_defaults", return_value=mock_config):
        with patch("src.cv_generator.__main__.resolve_output_paths", return_value=mock_paths):
            with patch("src.cv_generator.__main__.load_job_description", return_value="JD"):
                with pytest.raises(FileNotFoundError, match="PDF not found"):
                    validate_ats(mock_job_state, ats_target="pdf")


def test_validate_ats_handles_docx(mock_job_state: Mock):
    """Verify that validate_ats() can validate DOCX format."""
    docx_path = mock_job_state.job_dir / "cv" / "rendered" / "cv.docx"
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    docx_path.write_text("Mock DOCX", encoding="utf-8")

    mock_config = Mock()
    mock_paths = {
        "pdf": mock_job_state.job_dir / "cv" / "rendered" / "cv.pdf",
        "docx": docx_path,
        "ats": mock_job_state.job_dir / "cv" / "ats" / "report.json",
    }

    # Mock extract_docx_text to avoid trying to parse mock DOCX file
    with patch("src.steps.rendering.extract_docx_text", return_value="CV text"):
        with patch("src.steps.rendering.CVConfig.from_defaults", return_value=mock_config):
            with patch("src.cv_generator.__main__.resolve_output_paths", return_value=mock_paths):
                with patch("src.cv_generator.__main__.load_job_description", return_value="JD"):
                    with patch("src.cv_generator.ats.run_ats_analysis", return_value={"status": "ok"}):
                        with patch("src.cv_generator.ats.write_ats_report"):
                            result = validate_ats(
                                mock_job_state,
                                ats_target="docx",
                                via="docx",
                            )

    assert result["ats_target"] == "docx"


# ── template_test tests ──


def test_template_test_produces_report(mock_job_state: Mock):
    """Verify that template_test() produces a template test report."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    mock_parity = {
        "available": True,
        "pdf": {
            "available": True,
            "pct_overlap": 95,
            "order_match": 0.92,
        },
    }

    with patch("src.steps.rendering.run"):
        with patch("src.steps.rendering.CVConfig.from_defaults"):
            with patch("src.cv_generator.__main__.resolve_output_paths"):
                with patch("src.cv_generator.__main__._validate_render_parity", return_value=mock_parity):
                    with patch("src.cv_generator.__main__._template_score", return_value=95.0):
                        report = template_test(
                            mock_job_state,
                            via="docx",
                            target="pdf",
                        )

    assert report["template_score_pct"] == 95.0
    assert report["is_perfect"] == False
    assert report["target"] == "pdf"
    assert report["job_id"] == "test_job_201084"


def test_template_test_enforces_perfect(mock_job_state: Mock):
    """Verify that template_test() raises error if require_perfect=True and score < 100."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    mock_parity = {
        "available": True,
        "pdf": {"available": True, "pct_overlap": 90},
    }

    with patch("src.steps.rendering.run"):
        with patch("src.steps.rendering.CVConfig.from_defaults"):
            with patch("src.cv_generator.__main__.resolve_output_paths"):
                with patch("src.cv_generator.__main__._validate_render_parity", return_value=mock_parity):
                    with patch("src.cv_generator.__main__._template_score", return_value=90.0):
                        with pytest.raises(RuntimeError, match="expected 100.0%"):
                            template_test(
                                mock_job_state,
                                via="docx",
                                target="pdf",
                                require_perfect=True,
                            )


def test_template_test_passes_perfect(mock_job_state: Mock):
    """Verify that template_test() returns report when perfect and require_perfect=True."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    mock_parity = {
        "available": True,
        "pdf": {"available": True, "pct_overlap": 100},
    }

    with patch("src.steps.rendering.run"):
        with patch("src.steps.rendering.CVConfig.from_defaults"):
            with patch("src.cv_generator.__main__.resolve_output_paths"):
                with patch("src.cv_generator.__main__._validate_render_parity", return_value=mock_parity):
                    with patch("src.cv_generator.__main__._template_score", return_value=100.0):
                        report = template_test(
                            mock_job_state,
                            via="docx",
                            target="pdf",
                            require_perfect=True,
                        )

    assert report["is_perfect"] == True


def test_template_test_handles_unavailable_parity(mock_job_state: Mock):
    """Verify that template_test() raises error if parity check is unavailable."""
    to_render_path = mock_job_state.job_dir / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text("# John Doe", encoding="utf-8")

    mock_parity = {
        "available": False,
        "reason": "to_render.md not found",
    }

    with patch("src.steps.rendering.run"):
        with patch("src.steps.rendering.CVConfig.from_defaults"):
            with patch("src.cv_generator.__main__.resolve_output_paths"):
                with patch("src.cv_generator.__main__._validate_render_parity", return_value=mock_parity):
                    with pytest.raises(RuntimeError, match="unavailable"):
                        template_test(mock_job_state, via="docx", target="pdf")
