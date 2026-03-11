"""Tests for generate_documents contracts."""

from __future__ import annotations

import pytest

from src.nodes.generate_documents.contract import DocumentDeltas


def test_document_deltas_rejects_cv_summary_over_three_lines() -> None:
    with pytest.raises(ValueError, match="cv_summary"):
        DocumentDeltas(
            cv_summary="line1\nline2\nline3\nline4",
            cv_injections=[{"experience_id": "EXP001", "new_bullets": ["Did x"]}],
            letter_deltas={
                "subject_line": "Subject",
                "intro_paragraph": "Intro",
                "core_argument_paragraph": "Core",
                "alignment_paragraph": "Align",
                "closing_paragraph": "Close",
            },
            email_body="line1\nline2",
        )


def test_document_deltas_rejects_email_body_over_two_lines() -> None:
    with pytest.raises(ValueError, match="email_body"):
        DocumentDeltas(
            cv_summary="line1\nline2",
            cv_injections=[{"experience_id": "EXP001", "new_bullets": ["Did x"]}],
            letter_deltas={
                "subject_line": "Subject",
                "intro_paragraph": "Intro",
                "core_argument_paragraph": "Core",
                "alignment_paragraph": "Align",
                "closing_paragraph": "Close",
            },
            email_body="line1\nline2\nline3",
        )
