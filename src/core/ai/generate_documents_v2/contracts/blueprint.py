"""Blueprint contracts for macroplanning generated documents."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SectionBlueprint(BaseModel):
    """One planned document section before drafting."""

    section_id: str
    logical_train_of_thought: list[str]
    section_intent: str
    target_style: str | None = None
    word_count_target: int | None = None


class GlobalBlueprint(BaseModel):
    """Full planned structure for one application document set."""

    application_id: str
    strategy_type: str
    chosen_strategy: str = "generic"
    job_title: str | None = None
    source: str | None = None
    sections: list[SectionBlueprint] = Field(default_factory=list)
