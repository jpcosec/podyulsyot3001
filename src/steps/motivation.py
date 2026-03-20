"""Motivation step: Generate motivation letter content from matching results.

This step uses motivation processing logic from src/steps/motivation_service.py
and adds comment reading for iterative feedback refinement.

Reads:
- job.md — Job posting tracker with requirements and metadata
- planning/reviewed_mapping.json — Approved claims and summary from matching step
- profile data — Candidate profile from reference_data
- planning comments — Inline feedback for iteration

Produces:
- planning/motivation_letter.md — Rendered motivation letter (markdown)
- planning/motivation_letter.json — Structured output with fit signals and risk notes
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.steps.motivation_service import MotivationLetterService
from src.steps import StepResult
from src.utils.comments import append_to_comment_log
from src.utils.state import JobState

logger = logging.getLogger(__name__)


def run(state: JobState, *, force: bool = False) -> StepResult:
    """
    Generate motivation letter content.

    Reads: job.md, reviewed_mapping.json, profile, prompts, comments
    Produces: planning/motivation_letter.md, planning/motivation_letter.json

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist

    Returns:
        StepResult with status, produced files, comments_found, message
    """
    # Check if step already complete and not force
    if not force and state.step_complete("motivation"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"Motivation already complete for job {state.job_id}",
        )

    produced: list[str] = []
    comments_found = 0

    try:
        # Check for required input: reviewed_mapping.json
        mapping_path = state.artifact_path("planning/reviewed_mapping.json")
        if not mapping_path.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=(
                    f"reviewed_mapping.json not found for job {state.job_id}. "
                    "Run 'match-approve' first."
                ),
            )

        # Extract comments from previous outputs and input files for feedback
        comments_sources = [
            state.artifact_path("planning/motivation_letter.md"),
            mapping_path,
        ]
        comments = _extract_comments_from_files(comments_sources, state.job_dir)
        comments_found = len(comments)

        # Run the motivation letter service
        service = MotivationLetterService()
        result = service.generate_for_job(state.job_id, source=state.source)

        # Track produced files
        produced.append("planning/motivation_letter.md")
        produced.append("planning/motivation_letter.json")

        # Log comments to job-level comment log
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "motivation", comments)

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Generated motivation letter for job {state.job_id}",
        )

    except Exception as e:
        logger.exception(f"Failed to run motivation for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to generate motivation letter: {e}",
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
