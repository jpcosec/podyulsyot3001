"""Canonical extract-bridge helpers for schema-v0 jobs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.ai.match_skill.contracts import RequirementInput
from src.core.io import WorkspaceManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class ExtractBridgeError(Exception):
    """Raised when extract-bridge inputs are missing or invalid."""


def extract_bridge(
    source: str,
    job_id: str,
    workspace: WorkspaceManager | None = None,
) -> list[RequirementInput]:
    """Build extract-bridge artifacts from canonical translated job artifacts."""

    manager = workspace or WorkspaceManager()
    try:
        raw_data = manager.read_json(
            source,
            job_id,
            "nodes/translate/proposed/state.json",
        )
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error(
            f"{LogTag.FAIL} Extract bridge failed to load translated state: {exc}"
        )
        raise ExtractBridgeError(f"Failed to load translated state: {exc}") from exc

    requirements = extract_requirements_from_job_posting(raw_data)
    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": [item.model_dump() for item in requirements],
        "job_posting": raw_data,
    }
    manager.write_json(
        source,
        job_id,
        "nodes/extract_bridge/proposed/state.json",
        state_payload,
    )

    content_path = manager.resolve_under_job(
        source,
        job_id,
        "nodes/translate/proposed/content.md",
    )
    if content_path.exists():
        manager.write_text(
            source,
            job_id,
            "nodes/extract_bridge/proposed/content.md",
            content_path.read_text(encoding="utf-8"),
        )

    logger.info(
        f"{LogTag.OK} Extracted bridge completed: {len(requirements)} requirements"
    )
    return requirements


def extract_requirements_from_job_posting(
    raw_data: dict[str, Any],
) -> list[RequirementInput]:
    """Transform a raw JobPosting-like payload into requirement inputs only."""

    requirements = raw_data.get("requirements", [])
    if not requirements:
        raise ExtractBridgeError("No requirements field in JobPosting")

    return [
        RequirementInput(
            id=f"REQ_{i:03d}",
            text=req,
            priority="must",
        )
        for i, req in enumerate(requirements, 1)
    ]


def translated_state_path(
    workspace: WorkspaceManager, source: str, job_id: str
) -> Path:
    """Return the canonical translated state path for a job."""

    return workspace.resolve_under_job(
        source, job_id, "nodes/translate/proposed/state.json"
    )
