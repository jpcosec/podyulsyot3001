"""Email draft step: Generate application email draft from motivation summary.

This step uses motivation processing logic from src/steps/motivation_service.py
and generates a simple, professional email draft for submitting the application.

Reads:
- planning/motivation_letter.json — Motivation output with summary
- job.md — Job posting for title and contact info
- planning comments — Inline feedback for iteration

Produces:
- planning/application_email.md — Email draft with To, Subject, body, closing
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
    Generate application email draft.

    Reads: planning/motivation_letter.json, job.md, comments
    Produces: planning/application_email.md

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist

    Returns:
        StepResult with status, produced files, comments_found, message
    """
    # Check if step already complete and not force
    if not force and state.step_complete("email_draft"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"Email draft already complete for job {state.job_id}",
        )

    produced: list[str] = []
    comments_found = 0

    try:
        # Check for required input: motivation_letter.json
        motivation_path = state.artifact_path("planning/motivation_letter.json")
        if not motivation_path.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=(
                    f"motivation_letter.json not found for job {state.job_id}. "
                    "Run 'motivate' first."
                ),
            )

        # Extract comments from previous output for feedback
        comments_sources = [
            state.artifact_path("planning/application_email.md"),
        ]
        comments = _extract_comments_from_files(comments_sources, state.job_dir)
        comments_found = len(comments)

        # Run the email draft service
        service = MotivationLetterService()
        result = service.generate_email_draft(state.job_id, source=state.source)

        # Track produced files
        produced.append("planning/application_email.md")

        # Log comments to job-level comment log
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "email_draft", comments)

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Generated email draft for job {state.job_id}",
        )

    except Exception as e:
        logger.exception(f"Failed to run email_draft for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to generate email draft: {e}",
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
