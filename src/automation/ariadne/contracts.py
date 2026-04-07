"""Replay contracts Ariadne exposes to deterministic motors.

These DTOs give motors a narrow, stable execution surface without depending on
the full Ariadne domain model module.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ReplayIntent = Literal[
    "click",
    "fill",
    "fill_react_controlled",
    "select",
    "upload",
    "upload_letter",
    "press_key",
    "scroll",
    "wait",
    "navigate",
]


class ReplayTarget(BaseModel):
    """Motor-facing target descriptor for text or CSS resolution."""

    css: str | None = Field(default=None, description="CSS selector if available.")
    text: str | None = Field(
        default=None, description="Human-visible text for fuzzy matching."
    )


class ReplayAction(BaseModel):
    """Motor-facing action DTO with optional fallback behavior."""

    intent: ReplayIntent
    target: ReplayTarget | None = None
    value: str | None = Field(default=None, description="Rendered or templated value.")
    fallback: "ReplayAction | None" = None
    optional: bool = False


class ReplayObserve(BaseModel):
    """Observation contract motors use before executing a step."""

    required_elements: list[ReplayTarget] = Field(default_factory=list)


class ReplayStep(BaseModel):
    """Minimal step contract deterministic motors need for replay."""

    step_index: int
    name: str
    description: str
    observe: ReplayObserve
    actions: list[ReplayAction] = Field(default_factory=list)
    human_required: bool = False
    dry_run_stop: bool = False


class ReplayPath(BaseModel):
    """Minimal path contract used by replayer-oriented tests and tooling."""

    id: str
    task_id: str
    steps: list[ReplayStep]


def adapt_replay_step(step: Any) -> ReplayStep:
    """Adapt a domain step or compatible object into the replay contract."""

    return ReplayStep.model_validate(step, from_attributes=True)


def adapt_replay_path(path: Any) -> ReplayPath:
    """Adapt a domain path or compatible object into the replay contract."""

    return ReplayPath.model_validate(path, from_attributes=True)
