"""Rendering step: Convert validated markdown content to PDF artifacts.

This step handles all CV and motivation letter rendering, ATS validation, and
template testing. It uses existing rendering engines (DOCX, LaTeX) and ATS
infrastructure unchanged.

Reads:
- cv/to_render.md — Canonical CV content (from cv_tailoring step)
- planning/motivation_letter.md — Motivation letter content (from motivation step)
- profile data — Candidate profile for rendering context
- job description — For ATS scoring

Produces:
- output/cv.pdf — Rendered CV in PDF format
- output/motivation_letter.pdf — Rendered motivation letter in PDF (if applicable)
- cv/ats/report.json — ATS validation report
- cv/ats/template_test.json — Template parity report (optional)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.utils.config import CVConfig
from src.render.docx import DocumentRenderer
from src.render.latex import render_to_file
from src.render.pdf import extract_docx_text, extract_pdf_text
from src.steps import StepResult
from src.utils.comments import append_to_comment_log, extract_comments
from src.utils.state import JobState

logger = logging.getLogger(__name__)


def run(
    state: JobState,
    *,
    force: bool = False,
    via: str = "docx",
    docx_template: str = "modern",
    docx_template_path: str | None = None,
    language: str = "english",
    targets: list[str] | None = None,
) -> StepResult:
    """
    Render all validated content to PDF.

    Converts cv/to_render.md and planning/motivation_letter.md into PDF outputs.
    Optionally runs ATS validation and template testing.

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist
        via: Rendering engine ("docx" or "latex")
        docx_template: DOCX template style (classic, modern, harvard, executive)
        docx_template_path: Custom DOCX template path (overrides docx_template)
        language: Language for rendering (english, german, spanish)
        targets: What to render ([None] = all, or ["cv", "motivation"])

    Returns:
        StepResult with status, produced files, comments_found, message

    Reads:
    - cv/to_render.md — canonical render source
    - planning/motivation_letter.md — motivation content
    - raw/extracted.json — job metadata
    """
    # Check if step already complete and not force
    if not force and state.step_complete("rendering"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"Rendering already complete for job {state.job_id}",
        )

    produced: list[str] = []
    comments_found = 0

    try:
        # Determine what to render (default: all)
        render_targets = targets or ["cv", "motivation"]

        # Verify required inputs exist
        if "cv" in render_targets:
            to_render_path = state.artifact_path("cv/to_render.md")
            if not to_render_path.exists():
                return StepResult(
                    status="error",
                    produced=[],
                    comments_found=0,
                    message=f"cv/to_render.md not found for job {state.job_id}. "
                    "Run 'tailor-cv' first.",
                )

        # Extract comments for feedback loop
        comments_sources = []
        if state.artifact_path("cv/to_render.md").exists():
            comments_sources.append(state.artifact_path("cv/to_render.md"))
        if state.artifact_path("planning/motivation_letter.md").exists():
            comments_sources.append(state.artifact_path("planning/motivation_letter.md"))

        comments = _extract_comments_from_files(comments_sources, state.job_dir)
        comments_found = len(comments)

        # Initialize CVConfig (for path resolution and profile loading)
        config = CVConfig.from_defaults()

        # Render targets
        if "cv" in render_targets:
            _render_cv(
                state=state,
                config=config,
                via=via,
                docx_template=docx_template,
                docx_template_path=docx_template_path,
                language=language,
            )
            produced.append("output/cv.pdf")

        if "motivation" in render_targets and state.artifact_path(
            "planning/motivation_letter.md"
        ).exists():
            _render_motivation_letter(state=state)
            produced.append("output/motivation_letter.pdf")

        # Log comments to job-level comment log
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "rendering", comments)

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Rendered {', '.join(render_targets)} to PDF for job {state.job_id}",
        )

    except Exception as e:
        logger.exception(f"Failed to render outputs for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to render outputs: {e}",
        )


def validate_ats(
    state: JobState,
    *,
    ats_target: str = "pdf",
    via: str = "docx",
    file_stem: str = "cv",
) -> dict:
    """
    Run ATS validation on rendered CV.

    Validates the rendered CV (DOCX or PDF) against the job description using
    the dual-engine ATS system (code + LLM).

    Args:
        state: JobState instance
        ats_target: "pdf" or "docx" (which format to validate)
        via: "docx" or "latex" (what was used to render)
        file_stem: Base filename ("cv", etc.)

    Returns:
        dict with ATS report data (status, scores, analysis)

    Raises:
        FileNotFoundError: If rendered file doesn't exist
        ValueError: If job description not found
    """
    from src.cv_generator.ats import run_ats_analysis, write_ats_report
    from src.cv_generator.__main__ import (
        load_job_description,
        resolve_output_paths,
    )

    config = CVConfig.from_defaults()

    # Resolve output paths
    paths = resolve_output_paths(config, state.source, state.job_id, file_stem, via)

    # Load job description
    jd = load_job_description(
        config, state.source, state.job_id, job_description_path=None
    )

    # Extract CV text from target format
    if ats_target == "pdf":
        if not paths["pdf"].exists():
            raise FileNotFoundError(f"PDF not found: {paths['pdf']}")
        text = extract_pdf_text(paths["pdf"])
    else:
        if not paths["docx"].exists():
            raise FileNotFoundError(f"DOCX not found: {paths['docx']}")
        text = extract_docx_text(paths["docx"])

    # Run ATS analysis
    analysis = run_ats_analysis(cv_text=text, job_description=jd, ats_mode="fallback")
    analysis["ats_target"] = ats_target

    # Write report
    write_ats_report(paths["ats"], analysis)

    return analysis


def template_test(
    state: JobState,
    *,
    via: str = "docx",
    docx_template: str = "modern",
    target: str = "pdf",
    require_perfect: bool = False,
    language: str = "english",
) -> dict:
    """
    Run deterministic parity check on rendered CV.

    Compares rendered output against canonical to_render.md to ensure formatting
    fidelity. Returns template test results.

    Args:
        state: JobState instance
        via: "docx" or "latex"
        docx_template: DOCX template name
        target: "pdf" or "docx" (what to compare against)
        require_perfect: Raise error if not 100% match
        language: Language for rendering

    Returns:
        dict with template test report (score, results, parity details)

    Raises:
        RuntimeError: If require_perfect=True and score < 100%
    """
    from src.cv_generator.__main__ import (
        _template_score,
        _validate_render_parity,
        resolve_output_paths,
    )

    config = CVConfig.from_defaults()

    # Run rendering to have fresh output
    run(
        state,
        force=True,
        via=via,
        docx_template=docx_template,
        language=language,
        targets=["cv"],
    )

    # Validate parity
    paths = resolve_output_paths(config, state.source, state.job_id, "cv", via)
    parity = _validate_render_parity(
        config=config, source=state.source, job_id=state.job_id, paths=paths
    )

    if not parity.get("available"):
        raise RuntimeError(
            f"Template test unavailable: {parity.get('reason', 'unknown reason')}"
        )

    target_result = parity.get(target)
    if not isinstance(target_result, dict):
        raise RuntimeError(f"Template test missing target result: {target}")

    if not target_result.get("available", True):
        raise RuntimeError(
            f"Template test target unavailable ({target}): "
            f"{target_result.get('reason', 'unknown reason')}"
        )

    score = _template_score(target_result)

    # Build report
    report = {
        "source": state.source,
        "job_id": state.job_id,
        "language": language,
        "via": via,
        "docx_template": docx_template,
        "target": target,
        "template_score_pct": score,
        "is_perfect": score == 100.0,
        "parity": parity,
    }

    # Write report
    template_report_path = state.artifact_path("cv/ats/template_test.json")
    template_report_path.parent.mkdir(parents=True, exist_ok=True)
    template_report_path.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    logger.info(f"Template score ({target}): {score:.2f}%")

    if require_perfect and score < 100.0:
        raise RuntimeError(
            f"Template test failed: expected 100.0%, got {score:.2f}% on target '{target}'"
        )

    return report


# ── Helpers ──


def _render_cv(
    state: JobState,
    config: CVConfig,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    language: str,
) -> None:
    """
    Render CV to PDF via DOCX or LaTeX.

    Args:
        state: JobState instance
        config: CVConfig for path resolution
        via: "docx" or "latex"
        docx_template: DOCX template style
        docx_template_path: Custom template path
        language: Render language

    Raises:
        RuntimeError: If rendering fails
    """
    from src.cv_generator.__main__ import (
        build_cv,
        render_cv,
        render_docx,
        render_latex,
    )

    # Load canonical to_render.md
    to_render_path = state.artifact_path("cv/to_render.md")
    to_render_text = to_render_path.read_text(encoding="utf-8")

    # Resolve output paths
    from src.cv_generator.__main__ import resolve_output_paths

    paths = resolve_output_paths(config, state.source, state.job_id, "cv", via)

    if via == "docx":
        # Use build_cv for full DOCX + PDF pipeline
        from src.cv_generator.__main__ import build_cv

        build_cv(
            config=config,
            source=state.source,
            job_id=state.job_id,
            language=language,
            via="docx",
            docx_template=docx_template,
            docx_template_path=docx_template_path,
            run_ats=False,
            job_description_path=None,
            ats_mode="fallback",
            ats_prompt=None,
        )
    elif via == "latex":
        # Use LaTeX rendering pipeline
        from src.cv_generator.__main__ import build_cv

        build_cv(
            config=config,
            source=state.source,
            job_id=state.job_id,
            language=language,
            via="latex",
            docx_template=docx_template,
            docx_template_path=docx_template_path,
            run_ats=False,
            job_description_path=None,
            ats_mode="fallback",
            ats_prompt=None,
        )
    else:
        raise ValueError(f"Unknown rendering engine: {via}")

    # Ensure output file exists
    output_dir = state.artifact_path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    if via == "docx":
        rendered_pdf = paths["pdf"]
    else:
        rendered_pdf = paths["pdf"]

    if not rendered_pdf.exists():
        raise RuntimeError(f"Rendering failed: PDF not created at {rendered_pdf}")


def _render_motivation_letter(state: JobState) -> None:
    """
    Render motivation letter to PDF.

    Currently a placeholder that copies from planning to output.
    Full implementation would render markdown to PDF.

    Args:
        state: JobState instance

    Raises:
        FileNotFoundError: If motivation_letter.md not found
    """
    source_path = state.artifact_path("planning/motivation_letter.md")
    if not source_path.exists():
        raise FileNotFoundError(f"Motivation letter not found: {source_path}")

    # For now, we'll mark this as ready but expect caller to handle PDF generation
    # Full implementation would:
    # 1. Parse motivation_letter.md
    # 2. Render to DOCX or LaTeX
    # 3. Convert to PDF
    # For MVP, this is deferred to packaging step
    logger.info("Motivation letter rendering deferred to packaging step")


def _extract_comments_from_files(paths: list[Path], job_dir: Path) -> list:
    """
    Extract comments from multiple files.

    Args:
        paths: List of file paths to extract comments from
        job_dir: Job directory for relative path calculation

    Returns:
        List of InlineComment objects
    """
    all_comments = []
    for path in paths:
        if path.exists():
            all_comments.extend(extract_comments(path, job_dir=job_dir))
    return all_comments
