"""Matching step: Generate match proposal and approve reviewed mapping.

This step wraps the MatchProposalPipeline class from utils/pipeline.py
and adds comment reading for iterative feedback refinement.

Produces:
- planning/match_proposal.md — Human-reviewable proposal with requirements, evidence, and decision checkboxes
- planning/keywords.json — Extracted keywords and categories from the mapping
- planning/reviewed_mapping.json — Parsed and locked approved claims (after approve)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.utils.pipeline import MatchProposalPipeline, parse_reviewed_proposal
from src.steps import StepResult
from src.steps.keywords import extract_keywords_from_proposal
from src.utils.comments import extract_comments, append_to_comment_log
from src.utils.state import JobState

logger = logging.getLogger(__name__)


def run(state: JobState, *, force: bool = False) -> StepResult:
    """
    Generate match proposal from job + profile.

    Reads comments from own previous output and input files.
    Produces: planning/match_proposal.md, planning/keywords.json

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist
        comments_from_files: Optional list of additional files to extract comments from

    Returns:
        StepResult with status, produced files, comments_found, message
    """
    # Check if step already complete and not force
    if not force and state.step_complete("matching"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"Matching already complete for job {state.job_id}",
        )

    produced: list[str] = []
    comments_found = 0

    try:
        # Extract comments from previous proposal (if exists) and job.md for feedback
        comments_sources = [
            state.artifact_path("planning/match_proposal.md"),
            state.artifact_path("job.md"),
        ]
        comments = extract_comments_from_files(comments_sources, state.job_dir)
        comments_found = len(comments)

        # Log comments even if proposal generation fails
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "matching", comments)

        # Run the matching pipeline
        pipeline = MatchProposalPipeline()
        proposal_path = pipeline.execute_proposal(state.job_id, source=state.source)

        # Track produced files
        if proposal_path.exists():
            produced.append("planning/match_proposal.md")

        # Extract keywords from the proposal via dedicated keywords module
        keywords_data = extract_keywords_from_proposal(proposal_path)
        state.write_json_artifact("planning/keywords.json", keywords_data)
        produced.append("planning/keywords.json")

        # Any regenerated proposal invalidates previous approval lock
        reviewed_mapping_path = state.artifact_path("planning/reviewed_mapping.json")
        if reviewed_mapping_path.exists():
            reviewed_mapping_path.unlink()

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Generated match proposal for job {state.job_id} with {len(keywords_data.get('keywords', []))} keywords",
        )

    except Exception as e:
        logger.exception(f"Failed to run matching for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to generate match proposal: {e}",
        )


def approve(state: JobState) -> StepResult:
    """
    Parse reviewed match_proposal.md and lock reviewed_mapping.json.

    Reads the human-reviewed match_proposal.md and extracts approved/edited/rejected
    claims, then serializes to reviewed_mapping.json.

    Produces: planning/reviewed_mapping.json (with status: reviewed)

    Args:
        state: JobState instance for the target job

    Returns:
        StepResult with status, produced files, message
    """
    produced: list[str] = []
    comments_found = 0

    try:
        proposal_path = state.artifact_path("planning/match_proposal.md")
        if not proposal_path.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"match_proposal.md not found for job {state.job_id}. Run 'match' first.",
            )

        comments = extract_comments(proposal_path, job_dir=state.job_dir)
        comments_found = len(comments)
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "match_approve", comments)

        # Parse the reviewed proposal
        reviewed_mapping = parse_reviewed_proposal(proposal_path)

        # Mark status as reviewed (not approved — that's a later decision)
        reviewed_mapping.status = "reviewed"

        # Write reviewed mapping
        mapping_data = reviewed_mapping.model_dump()
        state.write_json_artifact("planning/reviewed_mapping.json", mapping_data)
        produced.append("planning/reviewed_mapping.json")

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Approved and locked mapping for job {state.job_id}: {len(reviewed_mapping.claims)} claims reviewed",
        )

    except Exception as e:
        logger.exception(f"Failed to approve matching for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to parse reviewed mapping: {e}",
        )


def extract_comments_from_files(paths: list[Path], job_dir: Path) -> list:
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
        all_comments.extend(extract_comments(path, job_dir=job_dir))
    return all_comments


def _extract_keywords_from_proposal(proposal_path: Path) -> dict[str, Any]:
    """Backwards-compatible wrapper for keyword extraction helper."""
    return extract_keywords_from_proposal(proposal_path)
