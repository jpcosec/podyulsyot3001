"""Deterministic review indicators for generated documents.

These helpers flag common quality and policy issues based on static checks.
"""

from __future__ import annotations

import re
from typing import Any

from src.ai.generate_documents.contracts import (
    DocumentDeltas,
    TextReviewIndicator,
)

FORBIDDEN_PHRASES = (
    "excellent", "expert", "passionate", "perfect", "ideal", "highly skilled",
    "incredible", "proven track record", "successful", "driven", "dynamic",
    "enthusiastic", "demonstrated", "extensive experience", "highly motivated",
)

def build_deterministic_indicators(
    deltas: DocumentDeltas,
) -> list[TextReviewIndicator]:
    """Flag quality and policy issues in generated document deltas."""
    indicators: list[TextReviewIndicator] = []

    # 1. Anti-fluff phrase detection
    all_text = _flatten_deltas_text(deltas)
    for idx, phrase in enumerate(FORBIDDEN_PHRASES, start=1):
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in phrase.split()) + r"\b"
        if re.search(pattern, all_text, flags=re.IGNORECASE):
            indicators.append(
                TextReviewIndicator(
                    severity="major",
                    category="tone",
                    rule_id=f"ANTI_FLUFF_{idx:03d}",
                    target_ref="global",
                    message=f"Detected forbidden style phrase: '{phrase}'",
                )
            )

    # 2. Length constraints
    summary_lines = [line for line in deltas.cv_summary.splitlines() if line.strip()]
    if len(summary_lines) > 3:
        indicators.append(
            TextReviewIndicator(
                severity="major",
                category="format",
                rule_id="LINE_LIMIT_001",
                target_ref="cv_summary",
                message="CV summary exceeds 3 non-empty lines",
            )
        )

    email_lines = [line for line in deltas.email_body.splitlines() if line.strip()]
    if len(email_lines) > 2:
        indicators.append(
            TextReviewIndicator(
                severity="major",
                category="format",
                rule_id="LINE_LIMIT_002",
                target_ref="email_body",
                message="Email body exceeds 2 non-empty lines",
            )
        )

    return indicators

def _flatten_deltas_text(deltas: DocumentDeltas) -> str:
    """Concatenate all textual outputs of the generation for analysis."""
    out: list[str] = [deltas.cv_summary, deltas.email_body]
    
    # Letter paragraphs
    out.extend([
        deltas.letter_deltas.subject_line,
        deltas.letter_deltas.intro_paragraph,
        deltas.letter_deltas.core_argument_paragraph,
        deltas.letter_deltas.alignment_paragraph,
        deltas.letter_deltas.closing_paragraph,
    ])
    
    # CV injections
    for inj in deltas.cv_injections:
        out.extend(inj.new_bullets)
        
    return "\n".join(out)
