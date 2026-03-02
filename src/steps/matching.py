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

from src.utils.pipeline import MatchProposalPipeline, parse_reviewed_proposal
from src.steps import StepResult
from src.utils.comments import extract_comments, append_to_comment_log, format_comments_for_prompt
from src.utils.state import JobState, PIPELINE_ROOT

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

        # Run the matching pipeline
        pipeline = MatchProposalPipeline()
        proposal_path = pipeline.execute_proposal(state.job_id, source=state.source)

        # Track produced files
        if proposal_path.exists():
            produced.append("planning/match_proposal.md")

        # Extract keywords from the proposal
        keywords_data = _extract_keywords_from_proposal(proposal_path)
        keywords_path = state.write_json_artifact("planning/keywords.json", keywords_data)
        produced.append("planning/keywords.json")

        # Log comments to job-level comment log
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "matching", comments)

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

    try:
        proposal_path = state.artifact_path("planning/match_proposal.md")
        if not proposal_path.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"match_proposal.md not found for job {state.job_id}. Run 'match' first.",
            )

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
            comments_found=0,
            message=f"Approved and locked mapping for job {state.job_id}: {len(reviewed_mapping.claims)} claims reviewed",
        )

    except Exception as e:
        logger.exception(f"Failed to approve matching for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=0,
            message=f"Failed to parse reviewed mapping: {e}",
        )


def extract_comments_from_files(
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
        all_comments.extend(extract_comments(path, job_dir=job_dir))
    return all_comments


def _extract_keywords_from_proposal(proposal_path: Path) -> dict[str, any]:
    """
    Extract keywords and categories from a match proposal.

    Scans the Requirements Mapping section for full/partial coverage items
    and builds a keywords list from requirement text.

    Args:
        proposal_path: Path to match_proposal.md

    Returns:
        Dict with structure: {"keywords": [...], "categories": [...], "match_strength": float}
    """
    if not proposal_path.exists():
        return {"keywords": [], "categories": [], "match_strength": 0.0}

    try:
        content = proposal_path.read_text(encoding="utf-8")
    except Exception:
        return {"keywords": [], "categories": [], "match_strength": 0.0}

    # Parse requirements mapping section
    import re

    keywords: set[str] = set()
    categories: set[str] = set()
    full_count = 0
    partial_count = 0
    total_count = 0

    # Pattern: ### R1: requirement text [COVERAGE]
    heading_pattern = re.compile(
        r"^###\s+((?:R|req_)\d+):\s*(.*?)\s+\[([A-Z]+)\]\s*$",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    for match in heading_pattern.finditer(content):
        req_id = match.group(1)
        req_text = match.group(2)
        coverage = match.group(3).upper()

        total_count += 1
        if coverage == "FULL":
            full_count += 1
        elif coverage == "PARTIAL":
            partial_count += 1

        # Extract keywords from requirement text (basic: split on spaces, filter short words)
        words = [w.lower() for w in req_text.split() if len(w) > 3]
        keywords.update(words)

        # Infer categories from coverage + requirement text
        if "python" in req_text.lower():
            categories.add("Programming")
        if any(x in req_text.lower() for x in ["process", "control", "engineering"]):
            categories.add("Technical")
        if any(x in req_text.lower() for x in ["degree", "education", "master"]):
            categories.add("Education")
        if any(x in req_text.lower() for x in ["experience", "year", "skilled"]):
            categories.add("Experience")

    # Calculate match strength as proportion of full/partial coverage
    if total_count > 0:
        match_strength = (full_count + 0.5 * partial_count) / total_count
    else:
        match_strength = 0.0

    return {
        "keywords": sorted(list(keywords)),
        "categories": sorted(list(categories)),
        "match_strength": round(match_strength, 2),
    }
