"""LangChain prompt helpers for the match skill.

This module keeps prompt construction separate from graph orchestration so the
matching workflow can remain LangChain-native while staying easy to unit test.
"""

from __future__ import annotations

from typing import Iterable

from langchain_core.prompts import ChatPromptTemplate

from src.match_skill.contracts import FeedbackItem, ProfileEvidence, RequirementInput


def build_match_prompt() -> ChatPromptTemplate:
    """Build the LCEL prompt used by the match model.

    Returns:
        A ``ChatPromptTemplate`` with one system message and one human message.
    """

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You assess job-fit against structured profile evidence. "
                "Return only data that satisfies the provided schema. "
                "Be strict about unsupported claims and keep reasoning concise.",
            ),
            (
                "human",
                "\n".join(
                    [
                        "Match the candidate profile to the job requirements.",
                        "",
                        "<job_requirements>",
                        "{requirements_block}",
                        "</job_requirements>",
                        "",
                        "<profile_evidence>",
                        "{profile_evidence_block}",
                        "</profile_evidence>",
                        "",
                        "<round_feedback>",
                        "{review_feedback_block}",
                        "</round_feedback>",
                        "",
                        "<regeneration_scope>",
                        "{regeneration_scope_block}",
                        "</regeneration_scope>",
                        "",
                        "Use only the listed evidence. If a requirement is unsupported, mark it missing.",
                    ]
                ),
            ),
        ]
    )


def build_prompt_input(
    requirements: Iterable[RequirementInput],
    profile_evidence: Iterable[ProfileEvidence],
    review_feedback: Iterable[FeedbackItem] | None = None,
    regeneration_scope: Iterable[str] | None = None,
) -> dict[str, str]:
    """Serialize typed inputs into prompt-friendly text blocks.

    Args:
        requirements: Structured job requirements.
        profile_evidence: Structured candidate evidence items.
        review_feedback: Optional feedback from previous review rounds.
        regeneration_scope: Optional list of requirement ids to re-evaluate.

    Returns:
        A mapping ready to feed into ``build_match_prompt()``.
    """

    return {
        "requirements_block": _format_requirements(requirements),
        "profile_evidence_block": _format_evidence(profile_evidence),
        "review_feedback_block": _format_feedback(review_feedback or []),
        "regeneration_scope_block": _format_scope(regeneration_scope or []),
    }


def _format_requirements(requirements: Iterable[RequirementInput]) -> str:
    """Render requirements into a compact line-oriented block."""

    lines = []
    for item in requirements:
        priority = f" priority={item.priority}" if item.priority else ""
        lines.append(f"- id={item.id}{priority} text={item.text}")
    return "\n".join(lines) or "- none"


def _format_evidence(profile_evidence: Iterable[ProfileEvidence]) -> str:
    """Render profile evidence into a compact line-oriented block."""

    lines = [f"- id={item.id} text={item.description}" for item in profile_evidence]
    return "\n".join(lines) or "- none"


def _format_feedback(review_feedback: Iterable[FeedbackItem]) -> str:
    """Render normalized review feedback for regeneration-aware prompts."""

    lines = []
    for item in review_feedback:
        patch = ""
        if item.patch_evidence is not None:
            patch = (
                f" patch_id={item.patch_evidence.id}"
                f" patch_text={item.patch_evidence.description}"
            )
        lines.append(
            f"- requirement_id={item.requirement_id} action={item.action}"
            f" note={item.reviewer_note or '-'}{patch}"
        )
    return "\n".join(lines) or "- none"


def _format_scope(regeneration_scope: Iterable[str]) -> str:
    """Render requirement ids that should remain in regeneration scope."""

    lines = [f"- {requirement_id}" for requirement_id in regeneration_scope]
    return "\n".join(lines) or "- none"
