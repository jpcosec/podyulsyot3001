"""Parser for reviewed match proposal markdown files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from src.models.pipeline_contract import ReviewedClaim, ReviewedMapping


def _extract_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    header_raw = parts[0].replace("---\n", "", 1)
    body = parts[1]
    data: dict[str, str] = {}
    for line in header_raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def _extract_line_value(block: str, prefix: str) -> str:
    for line in block.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_decision(block: str) -> str | None:
    match = re.search(
        r"Decision:\s*(approved|edited|rejected)",
        block,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).lower()

    decision_line = ""
    for line in block.splitlines():
        if line.strip().lower().startswith("decision:"):
            decision_line = line
            break

    text = decision_line or block
    checked = r"(?:\[\s*[xX]\s*\]|[xX]\s*\[\s*\])"
    decision_patterns = {
        "approved": ["approve", "approved"],
        "edited": ["edit", "edited"],
        "rejected": ["reject", "rejected"],
    }

    matches: list[tuple[int, str]] = []
    for decision, labels in decision_patterns.items():
        for label in labels:
            found = re.search(
                rf"{checked}\s*{label}\b",
                text,
                re.IGNORECASE,
            )
            if found:
                matches.append((found.start(), decision))

    if matches:
        matches.sort(key=lambda item: item[0])
        return matches[0][1]

    return None


def parse_reviewed_proposal(path: Path) -> ReviewedMapping:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _extract_frontmatter(text)
    job_id = frontmatter.get("job_id", "")
    status = frontmatter.get("status", "proposed")

    heading_pattern = re.compile(
        r"^###\s+((?:R|req_)\d+):\s*(.*?)\s+\[(FULL|PARTIAL|NONE)\]\s*$",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    matches = list(heading_pattern.finditer(body))

    claims: list[ReviewedClaim] = []
    for idx, heading in enumerate(matches):
        start = heading.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        block = body[start:end]
        decision = _parse_decision(block)
        if decision is None:
            continue

        evidence_ids_raw = _extract_line_value(block, "Evidence IDs")
        evidence_ids = [
            item.strip()
            for item in evidence_ids_raw.split(",")
            if item.strip() and item.strip().lower() != "none"
        ]
        claim_text = _extract_line_value(block, "Claim")
        edited_claim = _extract_line_value(block, "Edited Claim")
        notes = _extract_line_value(block, "Notes")

        if decision == "edited" and edited_claim:
            claim_text = edited_claim

        if decision == "approved":
            decision_literal: Literal["approved", "edited", "rejected"] = "approved"
        elif decision == "edited":
            decision_literal = "edited"
        else:
            decision_literal = "rejected"

        claims.append(
            ReviewedClaim(
                req_id=heading.group(1),
                decision=decision_literal,
                claim_text=claim_text,
                evidence_ids=evidence_ids,
                section="summary",
                notes=notes,
            )
        )

    gaps: list[str] = []
    gaps_match = re.search(
        r"##\s+Gaps\s*\(no evidence found\)(.*?)(\n##\s+|\Z)",
        body,
        flags=re.DOTALL,
    )
    if gaps_match:
        for line in gaps_match.group(1).splitlines():
            item = line.strip()
            if item.startswith("- "):
                gaps.append(item[2:].strip())

    summary = ""
    summary_match = re.search(
        r"##\s+Proposed Summary\s*(.*?)(\n##\s+|\Z)",
        body,
        flags=re.DOTALL,
    )
    if summary_match:
        summary = summary_match.group(1).strip()

    if status == "reviewed":
        status_literal: Literal["proposed", "reviewed", "approved"] = "reviewed"
    elif status == "approved":
        status_literal = "approved"
    else:
        status_literal = "proposed"

    return ReviewedMapping(
        job_id=job_id,
        status=status_literal,
        claims=claims,
        gaps=gaps,
        summary=summary,
    )
