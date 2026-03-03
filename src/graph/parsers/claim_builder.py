"""Helpers for deterministic claim text and evidence selection."""

from __future__ import annotations


def _valid_evidence_ids(
    preferred: list[str],
    fallback: list[str],
    evidence_by_id: dict[str, str],
) -> list[str]:
    preferred_valid = [item for item in preferred if item in evidence_by_id]
    if preferred_valid:
        return preferred_valid
    return [item for item in fallback if item in evidence_by_id]


def _confidence_from_coverage(coverage: str) -> str:
    if coverage == "full":
        return "strong"
    if coverage == "partial":
        return "moderate"
    return "weak"


def build_claim_text(
    requirement_text: str,
    evidence_lines: list[str],
    llm_claim: str | None = None,
    edited_claim: str | None = None,
) -> str:
    """Build claim text with priority: edited > llm > template fallback."""
    if edited_claim and edited_claim.strip():
        return edited_claim.strip()
    if llm_claim and llm_claim.strip():
        return llm_claim.strip()
    if evidence_lines:
        return f"{requirement_text} Evidence includes: {evidence_lines[0]}"
    return f"No direct evidence available yet for: {requirement_text}"


def _propose_claim_text(requirement_text: str, evidence_lines: list[str]) -> str:
    """Backwards-compatible alias for the previous helper name/signature."""
    return build_claim_text(requirement_text, evidence_lines)
