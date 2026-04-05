"""Typed BrowserOS playbook models for apply automation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ActionTool = Literal[
    "click",
    "fill",
    "select_option",
    "upload_file",
    "evaluate_script_react",
]


class PlaybookMeta(BaseModel):
    """Metadata describing one normalized BrowserOS/Ariadne playbook."""

    source: str
    flow: str
    version: str
    recorded: str
    job_example: str | None = None
    total_steps: int
    status: str
    notes: str | None = None


class PlaybookEntryPoint(BaseModel):
    """Entry-point hints used to detect or open the intended apply flow."""

    description: str | None = None
    url_pattern: str | None = None
    trigger_element_text: str | None = None
    ariadne_tag: str | None = None


class ExpectedElement(BaseModel):
    """One element that must be observable before a step can proceed."""

    text: str
    type: str | None = None


class ObserveBlock(BaseModel):
    """Snapshot observation requirements for a playbook step."""

    tool: Literal["take_snapshot"] = "take_snapshot"
    expected_elements: list[ExpectedElement] = Field(default_factory=list)


class PlaybookFallback(BaseModel):
    """Fallback action to try when the primary action target is absent."""

    tool: ActionTool
    selector_text: str
    value: str | None = None


class PlaybookAction(BaseModel):
    """Executable action inside a BrowserOS playbook step."""

    tool: ActionTool
    selector_text: str
    value: str | None = None
    note: str | None = None
    fallback: PlaybookFallback | None = None


class PlaybookStep(BaseModel):
    """One replayable step in a normalized BrowserOS playbook."""

    step: int
    name: str
    screenshot: str | None = None
    description: str
    ariadne_tag: str | None = None
    observe: ObserveBlock
    actions: list[PlaybookAction] = Field(default_factory=list)
    next_button_text: str | None = None
    human_required: bool | Literal["conditional"] = False
    human_trigger: str | None = None
    human_message: str | None = None
    dry_run_stop: bool = False
    notes: str | None = None


class BrowserOSPlaybook(BaseModel):
    """Full BrowserOS playbook used for deterministic apply replay."""

    meta: PlaybookMeta
    entry_point: PlaybookEntryPoint
    path: str
    steps: list[PlaybookStep]
    dead_ends_observed: list[dict] = Field(default_factory=list)
    bifurcations: dict[str, dict[str, str]] = Field(default_factory=dict)
