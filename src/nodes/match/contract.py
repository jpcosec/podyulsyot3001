"""Contracts for the match node."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RequirementMatch(BaseModel):#TODO: Seria interesante que el agente le ponga alguna valoracion a los requerimientos (nivel de importancia, asi como un sorting) Asi seria mas facil saber si se cumplen requisitos basicos:wq
    
    req_id: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    evidence_id: str | None = None
    reasoning: str

    @field_validator("evidence_id", mode="before")
    @classmethod
    def _normalize_evidence_id(cls, value: object) -> object:#TODO: Documentar, no se entiende para que es esto
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return ", ".join(parts) if parts else None
        return value


class MatchEnvelope(BaseModel):#TODO: Creo que hay un ligero drift entre esto y la logica real que estamos usando, Se usa esta clase?
    matches: list[RequirementMatch]
    total_score: float = Field(..., ge=0.0, le=1.0)
    decision_recommendation: Literal["proceed", "marginal", "reject"]
    summary_notes: str

    @field_validator("decision_recommendation", mode="before")
    @classmethod
    def _normalize_decision_recommendation(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        norm = value.strip().lower()
        mapping = {
            "proceed": "proceed",
            "proceder": "proceed",
            "continuar": "proceed",
            "marginal": "marginal",
            "borderline": "marginal",
            "reject": "reject",
            "rechazar": "reject",
            "rejected": "reject",
        }
        if norm in mapping:
            return mapping[norm]

        if any(token in norm for token in ("reject", "rechazar", "rejected")):
            return "reject"
        if any(
            token in norm
            for token in ("no recomendado", "not recommended", "no recommendation")
        ):
            return "reject"
        if any(token in norm for token in ("proceed", "proceder", "continuar")):
            return "proceed"
        if any(token in norm for token in ("recommended", "recomendado")):
            return "proceed"
        if any(token in norm for token in ("marginal", "borderline")):
            return "marginal"

        return value
