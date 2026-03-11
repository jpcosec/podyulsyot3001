"""Contracts for the extract_understand node."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    id: str
    text: str
    priority: Literal["must", "nice"]


class JobConstraint(BaseModel):
    constraint_type: str
    description: str


class JobUnderstandingExtract(BaseModel):#TODO: puede que ayude un poco aca hacer una especie de "preordenamiento"
    job_title: str
    analysis_notes: str = Field(#TODO: Faltan campos base como Tematica (puede ser un par de tags), descripcion, contacto y el formulario exacto que va arriba
        ...,
        description="Razonamiento logico detras de la extraccion y clasificacion",#TODO: ENGLISH PLEASE!
    )
    requirements: list[JobRequirement]
    constraints: list[JobConstraint]
    risk_areas: list[str] = Field(default_factory=list)
