"""Validated contracts for the document generation skill.

These models define the structured output from the tailored document engine
and the deterministic review indicators used to flag potential quality issues
(tone, formatting, grounding).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CVExperienceInjection(BaseModel):
    """Factual bullet point updates for a specific experience item."""

    experience_id: str = Field(
        ...,
        description="Must exactly match an experience id from the candidate profile.",
    )
    new_bullets: list[str] = Field(
        ...,
        min_length=1,
        description="Factual English bullet points integrating relevant evidence.",
    )

    @field_validator("experience_id")
    @classmethod
    def _validate_experience_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("experience_id must be non-empty")
        return cleaned

    @model_validator(mode="before")
    @classmethod
    def _normalize_bullet_field_aliases(cls, value: object) -> object:
        """Handle LLM drift by mapping common bullet-point field names to new_bullets."""
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "new_bullets" in payload:
            return payload

        # Common aliases produced by various models/prompts
        for alias in (
            "achievements",
            "bullets",
            "statements",
            "description_additions",
            "new_bullet",
        ):
            if alias not in payload:
                continue
            alias_value = payload.get(alias)
            if isinstance(alias_value, list):
                payload["new_bullets"] = alias_value
                return payload
            if isinstance(alias_value, str):
                payload["new_bullets"] = [alias_value]
                return payload
        return payload

    @field_validator("new_bullets")
    @classmethod
    def _normalize_new_bullets(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for bullet in value:
            text = " ".join(str(bullet).split()).strip()
            if text:
                cleaned.append(text)
        if not cleaned:
            raise ValueError("new_bullets must contain at least one non-empty bullet")
        return cleaned


class MotivationLetterDeltas(BaseModel):
    """Tailored components for the cover letter."""

    subject_line: str = Field(default="Application for Position")
    intro_paragraph: str = Field(
        ...,
        description="Concise English introduction identifying the target role.",
    )
    core_argument_paragraph: str = Field(
        ...,
        description="Technical argument in English aligned with the CV injections.",
    )
    alignment_paragraph: str = Field(
        ...,
        description="Factual alignment with the target institution/project goals.",
    )
    closing_paragraph: str = Field(default="Thank you for your consideration.")


class DocumentDeltas(BaseModel):
    """Unified container for all tailored document components."""

    cv_summary: str = Field(
        ...,
        description="Max 3 lines, factual English professional summary.",
    )
    cv_injections: list[CVExperienceInjection] = Field(default_factory=list)
    letter_deltas: MotivationLetterDeltas
    email_body: str = Field(
        ...,
        description="Max 2 lines, concise English email body for the application.",
    )

    @field_validator("cv_summary")
    @classmethod
    def _validate_summary_length(cls, value: str) -> str:
        lines = [line for line in value.splitlines() if line.strip()]
        if len(lines) > 3:
            raise ValueError("cv_summary must have at most 3 non-empty lines")
        return value

    @field_validator("email_body")
    @classmethod
    def _validate_email_length(cls, value: str) -> str:
        lines = [line for line in value.splitlines() if line.strip()]
        if len(lines) > 2:
            raise ValueError("email_body must have at most 2 non-empty lines")
        return value


class TextReviewIndicator(BaseModel):
    """Deterministic flag identifying a quality/policy violation in generated text."""

    severity: Literal["critical", "major", "minor"]
    category: Literal["grounding", "policy", "tone", "format", "consistency"]
    rule_id: str
    target_ref: str  # e.g. 'cv_summary', 'experience:EXP001'
    message: str
    evidence_refs: list[str] = Field(default_factory=list)


class TextReviewAssistEnvelope(BaseModel):
    """Collection of review indicators for a specific job run."""

    node: str = "generate_documents"
    job_id: str
    source_state_hash: str
    indicators: list[TextReviewIndicator]
    summary: str


class GeneratedDocuments(BaseModel):
    """Rendered outputs (Markdown) for final delivery."""

    cv_markdown: str
    letter_markdown: str
    email_markdown: str
