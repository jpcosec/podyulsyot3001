from __future__ import annotations

from pydantic import BaseModel, Field


class SectionBlueprint(BaseModel):
    section_id: str
    logical_train_of_thought: list[str]
    section_intent: str
    target_style: str | None = None
    word_count_target: int | None = None


class GlobalBlueprint(BaseModel):
    application_id: str
    strategy_type: str
    job_title: str | None = None
    source: str | None = None
    sections: list[SectionBlueprint] = Field(default_factory=list)
