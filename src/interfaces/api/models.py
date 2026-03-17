from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


StageStatus = Literal["pending", "running", "paused_review", "completed", "failed"]


@dataclass(frozen=True)
class StageItem:
    stage: str
    status: StageStatus
    artifact_ref: str | None


@dataclass(frozen=True)
class JobListItem:
    source: str
    job_id: str
    thread_id: str
    current_node: str
    status: str
    updated_at: str


@dataclass(frozen=True)
class JobTimeline:
    source: str
    job_id: str
    thread_id: str
    current_node: str
    status: str
    stages: list[StageItem]
    artifacts: dict[str, str]
    updated_at: str


@dataclass(frozen=True)
class TextSpanItem:
    requirement_id: str
    start_line: int
    end_line: int
    text_preview: str


@dataclass(frozen=True)
class RequirementItem:
    id: str
    text: str
    priority: str
    spans: list[TextSpanItem]


@dataclass(frozen=True)
class ViewTwoPayload:
    source: str
    job_id: str
    source_markdown: str
    requirements: list[RequirementItem]


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    kind: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    label: str
    score: float | None
    reasoning: str | None
    evidence_id: str | None


@dataclass(frozen=True)
class ViewOnePayload:
    source: str
    job_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@dataclass(frozen=True)
class ViewThreePayload:
    source: str
    job_id: str
    documents: dict[str, str]
    nodes: list[GraphNode]
    edges: list[GraphEdge]


def to_dict(
    value: JobListItem
    | JobTimeline
    | StageItem
    | TextSpanItem
    | RequirementItem
    | ViewTwoPayload
    | GraphNode
    | GraphEdge
    | ViewOnePayload
    | ViewThreePayload,
) -> dict:
    return asdict(value)
