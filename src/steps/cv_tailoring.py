"""CV tailoring step: Generate tailored CV content for a job posting.

This step wraps the CVTailoringPipeline class from cv_generator/pipeline.py
and adds comment reading for iterative feedback refinement.

Reads:
- job.md — Job posting tracker with requirements and metadata
- planning/reviewed_mapping.json — Approved claims from matching step (optional input)
- profile data — Candidate profile from reference_data
- planning comments — Inline feedback for iteration

Produces:
- planning/cv_tailoring.md — Brief summary of what was tailored
- cv/to_render.md — Canonical render source (markdown) for rendering step
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.utils.config import CVConfig
from src.utils.loaders.profile_loader import load_base_profile
from src.utils.model import CVModel
from src.cv_generator.pipeline import CVTailoringPipeline
from src.steps import StepResult
from src.utils.comments import extract_comments, append_to_comment_log
from src.utils.state import JobState

logger = logging.getLogger(__name__)


def run(state: JobState, *, force: bool = False, language: str = "english") -> StepResult:
    """
    Tailor CV content for this job.

    Reads: job.md, reviewed_mapping.json (optional), profile, comments
    Produces: planning/cv_tailoring.md, cv/to_render.md

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist
        language: CV language for rendering ('english', 'german', 'spanish')

    Returns:
        StepResult with status, produced files, comments_found, message
    """
    # Check if step already complete and not force
    if not force and state.step_complete("cv_tailoring"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"CV tailoring already complete for job {state.job_id}",
        )

    produced: list[str] = []
    comments_found = 0

    try:
        # Check for required input: job.md
        job_md_path = state.artifact_path("job.md")
        if not job_md_path.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"job.md not found for job {state.job_id}. Run 'ingest' first.",
            )

        # Extract comments from previous outputs and input files for feedback
        comments_sources = [
            state.artifact_path("planning/cv_tailoring.md"),
            state.artifact_path("planning/cv_content_preview.md"),
            job_md_path,
        ]
        comments = _extract_comments_from_files(comments_sources, state.job_dir)
        comments_found = len(comments)

        # Run the CV tailoring pipeline
        pipeline = CVTailoringPipeline()
        final_state = pipeline.execute(state.job_id, source=state.source)

        # The pipeline produces planning/cv_tailoring.md and cv/to_render.md
        # (via build_to_render_markdown which the pipeline calls)
        # Let's verify these were created
        tailoring_md = state.artifact_path("planning/cv_tailoring.md")
        to_render_md = state.artifact_path("cv/to_render.md")

        # If to_render.md wasn't created by the pipeline, we need to build it ourselves
        if not to_render_md.exists():
            config = CVConfig.from_defaults()
            profile = load_base_profile(config.profile_path())
            model = CVModel.from_profile(profile)

            # Import the build function (avoid circular import by importing here)
            from src.cv_generator.__main__ import build_to_render_markdown

            to_render_content = build_to_render_markdown(model)
            to_render_md.parent.mkdir(parents=True, exist_ok=True)
            to_render_md.write_text(to_render_content, encoding="utf-8")

        # Track produced files
        if tailoring_md.exists():
            produced.append("planning/cv_tailoring.md")
        if to_render_md.exists():
            produced.append("cv/to_render.md")

        # Log comments to job-level comment log
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "cv_tailoring", comments)

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Tailored CV content for job {state.job_id} ({len(final_state.proposed_claims)} claims generated)",
        )

    except Exception as e:
        logger.exception(f"Failed to run CV tailoring for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to tailor CV content: {e}",
        )


def _extract_comments_from_files(
    paths: list[Path], job_dir: Path
) -> list:
    """
    Extract comments from multiple files.

    Args:
        paths: List of file paths to extract comments from
        job_dir: Job directory for relative path calculation

    Returns:
        List of InlineComment objects
    """
    from src.utils.comments import extract_comments

    all_comments = []
    for path in paths:
        if path.exists():
            all_comments.extend(extract_comments(path, job_dir=job_dir))
    return all_comments
