"""Canonical extract-bridge helpers for schema-v0 jobs."""

from __future__ import annotations

import logging
from typing import Any

from src.core.ai.match_skill.contracts import RequirementInput
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class ExtractBridgeError(Exception):
    """Raised when extract-bridge inputs are missing or invalid."""


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
