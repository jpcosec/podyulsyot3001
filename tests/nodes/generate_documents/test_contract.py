"""Tests for generate_documents contracts."""

from __future__ import annotations

import pytest

from src.nodes.generate_documents.contract import DocumentDeltas


def test_document_deltas_rejects_cv_summary_over_three_lines() -> None:
    with pytest.raises(ValueError, match="cv_summary"):
        DocumentDeltas.model_validate(
            {
                "cv_summary": "line1\nline2\nline3\nline4",
                "cv_injections": [
                    {"experience_id": "EXP001", "new_bullets": ["Did x"]}
                ],
                "letter_deltas": {
                    "subject_line": "Subject",
                    "intro_paragraph": "Intro",
                    "core_argument_paragraph": "Core",
                    "alignment_paragraph": "Align",
                    "closing_paragraph": "Close",
                },
                "email_body": "line1\nline2",
            }
        )


def test_document_deltas_rejects_email_body_over_two_lines() -> None:
    with pytest.raises(ValueError, match="email_body"):
        DocumentDeltas.model_validate(
            {
                "cv_summary": "line1\nline2",
                "cv_injections": [
                    {"experience_id": "EXP001", "new_bullets": ["Did x"]}
                ],
                "letter_deltas": {
                    "subject_line": "Subject",
                    "intro_paragraph": "Intro",
                    "core_argument_paragraph": "Core",
                    "alignment_paragraph": "Align",
                    "closing_paragraph": "Close",
                },
                "email_body": "line1\nline2\nline3",
            }
        )


def test_document_deltas_normalizes_list_fields_and_alias_bullets() -> None:
    out = DocumentDeltas.model_validate(
        {
            "cv_summary": ["line1", "line2"],
            "cv_injections": [
                {
                    "experience_id": "EXP001",
                    "achievements_to_inject": ["Bullet A", "Bullet B"],
                }
            ],
            "letter_deltas": {
                "core_argument_paragraph": "Core argument",
            },
            "email_body": ["mail line1", "mail line2"],
        }
    )

    assert out.cv_summary == "line1\nline2"
    assert out.cv_injections[0].new_bullets == ["Bullet A", "Bullet B"]
    assert out.letter_deltas.subject_line == "Application"
    assert out.letter_deltas.intro_paragraph == "I am applying for this position."
    assert out.letter_deltas.alignment_paragraph == "Core argument"
    assert out.letter_deltas.closing_paragraph == "Thank you for your consideration."
    assert out.email_body == "mail line1\nmail line2"


def test_document_deltas_normalizes_statements_and_email_deltas() -> None:
    out = DocumentDeltas.model_validate(
        {
            "cv_summary": "line1",
            "cv_injections": [
                {
                    "experience_id": "EXP001",
                    "statements": ["Bullet A"],
                }
            ],
            "letter_deltas": {
                "core_argument_paragraph": "Core",
            },
            "email_deltas": {
                "email_body": ["mail line1", "mail line2"],
            },
        }
    )

    assert out.cv_injections[0].new_bullets == ["Bullet A"]
    assert out.email_body == "mail line1\nmail line2"


def test_document_deltas_normalizes_description_additions_alias() -> None:
    out = DocumentDeltas.model_validate(
        {
            "cv_summary": "line1",
            "cv_injections": [
                {
                    "experience_id": "EXP001",
                    "description_additions": ["Bullet A", "Bullet B"],
                }
            ],
            "letter_deltas": {
                "core_argument_paragraph": "Core",
            },
            "email_body": "mail line1",
        }
    )

    assert out.cv_injections[0].new_bullets == ["Bullet A", "Bullet B"]


def test_document_deltas_normalizes_unknown_string_bullet_field() -> None:
    out = DocumentDeltas.model_validate(
        {
            "cv_summary": "line1",
            "cv_injections": [
                {
                    "experience_id": "EXP001",
                    "injected_bullet": "Implemented backend APIs for applied analytics",
                }
            ],
            "letter_deltas": {
                "core_argument_paragraph": "Core",
            },
            "email_body": "mail line1",
        }
    )

    assert out.cv_injections[0].new_bullets == [
        "Implemented backend APIs for applied analytics"
    ]
