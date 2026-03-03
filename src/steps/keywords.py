"""Keyword extraction utilities for matching outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_keywords_from_proposal(proposal_path: Path) -> dict[str, Any]:
    """Extract keywords, categories, and match strength from proposal markdown."""
    if not proposal_path.exists():
        return {"keywords": [], "categories": [], "match_strength": 0.0}

    try:
        content = proposal_path.read_text(encoding="utf-8")
    except Exception:
        return {"keywords": [], "categories": [], "match_strength": 0.0}

    import re

    keywords: set[str] = set()
    categories: set[str] = set()
    full_count = 0
    partial_count = 0
    total_count = 0

    heading_pattern = re.compile(
        r"^###\s+((?:R|req_)\d+):\s*(.*?)\s+\[([A-Z]+)\]\s*$",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    for match in heading_pattern.finditer(content):
        req_text = match.group(2)
        coverage = match.group(3).upper()

        total_count += 1
        if coverage == "FULL":
            full_count += 1
        elif coverage == "PARTIAL":
            partial_count += 1

        words = [w.lower() for w in req_text.split() if len(w) > 3]
        keywords.update(words)

        req_text_lower = req_text.lower()
        if "python" in req_text_lower:
            categories.add("Programming")
        if any(x in req_text_lower for x in ["process", "control", "engineering"]):
            categories.add("Technical")
        if any(x in req_text_lower for x in ["degree", "education", "master"]):
            categories.add("Education")
        if any(x in req_text_lower for x in ["experience", "year", "skilled"]):
            categories.add("Experience")

    if total_count > 0:
        match_strength = (full_count + 0.5 * partial_count) / total_count
    else:
        match_strength = 0.0

    return {
        "keywords": sorted(list(keywords)),
        "categories": sorted(list(categories)),
        "match_strength": round(match_strength, 2),
    }
