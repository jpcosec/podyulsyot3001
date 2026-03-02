from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.models.job import JobPosting
from src.models.motivation import FitSignal


class FitAnalysis(BaseModel):
    """Output of the analyze-fit tool."""

    overall_score: int
    eligibility: Literal["pass", "risk", "fail"]
    alignment_summary: str
    top_matches: list[FitSignal]
    gaps: list[str]
    recommendation: Literal["strong_apply", "apply", "weak_apply", "skip"]


class ApplicationPlan(BaseModel):
    """One job's application plan within a batch."""

    job: JobPosting
    fit: FitAnalysis
    cv_strategy: str
    motivation_strategy: str
    priority: int


class ApplicationBatch(BaseModel):
    """Output of 'apply-to <urls>' planning phase."""

    plans: list[ApplicationPlan]
    skipped: list[dict]
