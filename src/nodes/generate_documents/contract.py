"""Contracts for the generate_documents node."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CVExperienceInjection(BaseModel):
    experience_id: str = Field(
        ...,
        description="Must exactly match an experience id from candidate_base_cv.experience",
    )
    new_bullets: list[str] = Field(
        ...,
        min_length=1,
        description="Factual English bullet points integrating human patches",
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
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "new_bullets" in payload:
            return payload

        for alias in (
            "achievements",
            "achievements_to_inject",
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

        for key, candidate in payload.items():
            if key == "experience_id":
                continue
            if not isinstance(candidate, list):
                continue
            if all(isinstance(item, str) for item in candidate):
                payload["new_bullets"] = candidate
                return payload

        for key, candidate in payload.items():
            if key == "experience_id":
                continue
            if not isinstance(candidate, str):
                continue
            text = " ".join(candidate.split()).strip()
            if text:
                payload["new_bullets"] = [text]
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
    subject_line: str
    intro_paragraph: str = Field(
        ...,
        description="Direct English introduction without fluff",
    )
    core_argument_paragraph: str = Field(
        ...,
        description="Technical argument in English aligned with cv_injections",
    )
    alignment_paragraph: str = Field(
        ...,
        description="Factual alignment with institution/project",
    )
    closing_paragraph: str

    @model_validator(mode="before")
    @classmethod
    def _normalize_missing_fields(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        core = str(payload.get("core_argument_paragraph", "")).strip()
        payload.setdefault("subject_line", "Application")
        payload.setdefault("intro_paragraph", "I am applying for this position.")
        payload.setdefault(
            "alignment_paragraph",
            core if core else "My background aligns with the role requirements.",
        )
        payload.setdefault("closing_paragraph", "Thank you for your consideration.")
        return payload


class DocumentDeltas(BaseModel):
    cv_summary: str = Field(
        ...,
        description="Max 3 lines, factual English summary",
    )
    cv_injections: list[CVExperienceInjection] = Field(default_factory=list)
    letter_deltas: MotivationLetterDeltas
    email_body: str = Field(
        ...,
        description="Max 2 lines, concise English email body",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_common_model_drift(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)

        cv_summary = payload.get("cv_summary")
        if isinstance(cv_summary, list):
            payload["cv_summary"] = "\n".join(
                " ".join(str(item).split()).strip()
                for item in cv_summary
                if str(item).strip()
            )

        email_body = payload.get("email_body")
        if email_body is None and isinstance(payload.get("email_deltas"), dict):
            email_body = payload["email_deltas"].get("email_body")
        if isinstance(email_body, list):
            email_body = "\n".join(
                " ".join(str(item).split()).strip()
                for item in email_body
                if str(item).strip()
            )
        if isinstance(email_body, str):
            payload["email_body"] = email_body

        return payload

    @model_validator(mode="after")
    def _validate_line_limits(self) -> "DocumentDeltas":
        cv_lines = [line for line in self.cv_summary.splitlines() if line.strip()]
        if len(cv_lines) > 3:
            raise ValueError("cv_summary must have at most 3 non-empty lines")

        email_lines = [line for line in self.email_body.splitlines() if line.strip()]
        if len(email_lines) > 2:
            raise ValueError("email_body must have at most 2 non-empty lines")

        return self


class TextReviewIndicator(BaseModel):
    severity: Literal["critical", "major", "minor"]
    category: Literal["grounding", "policy", "tone", "format", "consistency"]
    rule_id: str
    target_ref: str
    message: str
    evidence_refs: list[str] = Field(default_factory=list)


class TextReviewAssistEnvelope(BaseModel):
    node: str
    job_id: str
    source_state_hash: str
    indicators: list[TextReviewIndicator]
    summary: str
