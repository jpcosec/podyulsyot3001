from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
import re

from src.core.graph.state import build_thread_id
from src.interfaces.api.models import (
    GraphEdge,
    GraphNode,
    JobListItem,
    JobTimeline,
    RequirementItem,
    StageStatus,
    StageItem,
    TextSpanItem,
    ViewOnePayload,
    ViewThreePayload,
    ViewTwoPayload,
)

PIPELINE_STAGES: tuple[str, ...] = (
    "scrape",
    "translate_if_needed",
    "extract_understand",
    "match",
    "review_match",
    "generate_documents",
    "package",
)


def list_jobs(data_root: Path) -> list[JobListItem]:
    jobs: list[JobListItem] = []
    if not data_root.exists():
        return jobs

    for source_dir in sorted(path for path in data_root.iterdir() if path.is_dir()):
        for job_dir in sorted(path for path in source_dir.iterdir() if path.is_dir()):
            timeline = build_job_timeline(data_root, source_dir.name, job_dir.name)
            jobs.append(
                JobListItem(
                    source=timeline.source,
                    job_id=timeline.job_id,
                    thread_id=timeline.thread_id,
                    current_node=timeline.current_node,
                    status=timeline.status,
                    updated_at=timeline.updated_at,
                )
            )
    return jobs


def build_job_timeline(data_root: Path, source: str, job_id: str) -> JobTimeline:
    job_root = data_root / source / job_id
    nodes_root = job_root / "nodes"
    graph_root = job_root / "graph"

    stage_items = [
        StageItem(
            stage=stage,
            status=_resolve_stage_status(nodes_root, stage),
            artifact_ref=_primary_artifact_ref(nodes_root, stage),
        )
        for stage in PIPELINE_STAGES
    ]
    current_node, status = _resolve_current_state(stage_items)

    artifact_map = _collect_artifact_refs(nodes_root, graph_root)
    updated_at = _resolve_updated_at(job_root)

    return JobTimeline(
        source=source,
        job_id=job_id,
        thread_id=build_thread_id(source, job_id),
        current_node=current_node,
        status=status,
        stages=stage_items,
        artifacts=artifact_map,
        updated_at=updated_at,
    )


def _resolve_stage_status(nodes_root: Path, stage: str) -> StageStatus:
    if stage == "review_match":
        decision_json = nodes_root / "match" / "review" / "decision.json"
        decision_md = nodes_root / "match" / "review" / "decision.md"
        if decision_json.exists():
            return "completed"
        if decision_md.exists():
            return "paused_review"
        return "pending"

    approved = nodes_root / stage / "approved" / "state.json"
    if approved.exists():
        return "completed"

    proposed = nodes_root / stage / "proposed" / "state.json"
    if proposed.exists():
        return "running"

    return "pending"


def _primary_artifact_ref(nodes_root: Path, stage: str) -> str | None:
    if stage == "review_match":
        decision_json = nodes_root / "match" / "review" / "decision.json"
        if decision_json.exists():
            return str(decision_json)
        decision_md = nodes_root / "match" / "review" / "decision.md"
        if decision_md.exists():
            return str(decision_md)
        return None

    approved = nodes_root / stage / "approved" / "state.json"
    if approved.exists():
        return str(approved)

    proposed = nodes_root / stage / "proposed" / "state.json"
    if proposed.exists():
        return str(proposed)

    return None


def _resolve_current_state(stage_items: list[StageItem]) -> tuple[str, str]:
    for item in stage_items:
        if item.status in {"running", "paused_review", "failed"}:
            return item.stage, _map_run_status(item.status)

    for item in reversed(stage_items):
        if item.status == "completed":
            if item.stage == "package":
                return "package", "completed"
            return item.stage, "running"

    return "scrape", "running"


def _map_run_status(stage_status: str) -> str:
    if stage_status == "paused_review":
        return "pending_review"
    if stage_status == "failed":
        return "failed"
    return "running"


def _collect_artifact_refs(nodes_root: Path, graph_root: Path) -> dict[str, str]:
    output: dict[str, str] = {}
    checkpoint = graph_root / "checkpoint.sqlite"
    if checkpoint.exists():
        output["checkpoint"] = str(checkpoint)

    for stage in PIPELINE_STAGES:
        artifact = _primary_artifact_ref(nodes_root, stage)
        if artifact:
            output[stage] = artifact
    return output


def _resolve_updated_at(job_root: Path) -> str:
    files = [path for path in job_root.rglob("*") if path.is_file()]
    if not files:
        return datetime.now(UTC).isoformat()

    newest = max(files, key=lambda path: path.stat().st_mtime)
    return datetime.fromtimestamp(newest.stat().st_mtime, tz=UTC).isoformat()


def load_match_review_payload(data_root: Path, source: str, job_id: str) -> dict:
    job_root = data_root / source / job_id
    approved_state_path = job_root / "nodes" / "match" / "approved" / "state.json"
    decision_path = job_root / "nodes" / "match" / "review" / "decision.md"
    decision_json_path = job_root / "nodes" / "match" / "review" / "decision.json"

    approved_state = _read_json(approved_state_path)
    decision_md = (
        decision_path.read_text(encoding="utf-8") if decision_path.exists() else ""
    )
    decision_json = _read_json(decision_json_path)

    return {
        "source": source,
        "job_id": job_id,
        "approved_state": approved_state,
        "decision_markdown": decision_md,
        "decision_json": decision_json,
    }


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(value, dict):
        return value
    return {}


def build_view_two_payload(data_root: Path, source: str, job_id: str) -> ViewTwoPayload:
    job_root = data_root / source / job_id
    source_text_path = job_root / "raw" / "source_text.md"
    extract_path = job_root / "nodes" / "extract_understand" / "approved" / "state.json"

    source_markdown = (
        source_text_path.read_text(encoding="utf-8")
        if source_text_path.exists()
        else ""
    )
    extract_state = _read_json(extract_path)

    raw_requirements = extract_state.get("requirements")
    requirements: list[RequirementItem] = []
    if isinstance(raw_requirements, list):
        for item in raw_requirements:
            if not isinstance(item, dict):
                continue
            req_id = str(item.get("id", "")).strip()
            req_text = str(item.get("text", "")).strip()
            req_priority = str(item.get("priority", "")).strip()
            if not req_id or not req_text:
                continue
            spans = _derive_spans(req_id, req_text, source_markdown)
            requirements.append(
                RequirementItem(
                    id=req_id,
                    text=req_text,
                    priority=req_priority,
                    spans=spans,
                )
            )

    return ViewTwoPayload(
        source=source,
        job_id=job_id,
        source_markdown=source_markdown,
        requirements=requirements,
    )


def _derive_spans(
    requirement_id: str, requirement_text: str, source_markdown: str
) -> list[TextSpanItem]:
    lines = source_markdown.splitlines()
    if not lines:
        return []

    normalized_requirement = _normalize(requirement_text)
    exact_matches: list[TextSpanItem] = []
    for line_no, line in enumerate(lines, start=1):
        line_norm = _normalize(line)
        if _is_noise_line(line_norm):
            continue
        if normalized_requirement and normalized_requirement in line_norm:
            exact_matches.append(
                TextSpanItem(
                    requirement_id=requirement_id,
                    start_line=line_no,
                    end_line=line_no,
                    text_preview=line.strip()[:200],
                )
            )
    if exact_matches:
        return exact_matches

    keywords = _keywords(requirement_text)
    min_score = 2 if len(keywords) >= 3 else 1
    scored: list[tuple[int, str, int]] = []
    for line_no, line in enumerate(lines, start=1):
        line_norm = _normalize(line)
        if not line_norm or _is_noise_line(line_norm):
            continue
        score = sum(1 for token in keywords if token in line_norm)
        score += _synonym_score(keywords, line_norm)
        if score >= min_score:
            scored.append((line_no, line.strip(), score))

    scored.sort(key=lambda item: item[2], reverse=True)
    top = scored[:3]
    return [
        TextSpanItem(
            requirement_id=requirement_id,
            start_line=line_no,
            end_line=line_no,
            text_preview=text[:200],
        )
        for line_no, text, _score in top
    ]


def _normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", value.lower()).split())


def _keywords(requirement_text: str) -> list[str]:
    stop_words = {
        "the",
        "and",
        "with",
        "for",
        "that",
        "this",
        "have",
        "from",
        "your",
        "very",
        "good",
        "knowledge",
        "at",
        "least",
        "one",
        "or",
        "of",
        "previous",
        "area",
        "including",
        "evaluation",
        "level",
    }
    terms = [
        token
        for token in _normalize(requirement_text).split()
        if token not in stop_words
    ]
    return [token for token in terms if len(token) >= 3 or _is_cefr_token(token)][:8]


def _is_cefr_token(token: str) -> bool:
    return bool(re.fullmatch(r"[abc][12]", token))


def _is_noise_line(normalized_line: str) -> bool:
    if len(normalized_line) < 5:
        return True
    blocked_phrases = (
        "previous posting",
        "return to list",
        "you are here",
        "powered by",
        "contact",
        "imprint",
        "data protection",
        "accessibility",
    )
    return any(phrase in normalized_line for phrase in blocked_phrases)


def _synonym_score(keywords: list[str], normalized_line: str) -> int:
    hints = {
        "english": ("englisch",),
        "german": ("deutsch",),
        "computer": ("informatik",),
        "degree": ("abschluss", "studium"),
        "programming": ("programmier",),
        "knowledge": ("kenntnisse", "vorkenntnisse"),
        "distributed": ("verteilte",),
        "language": ("sprache",),
    }
    score = 0
    for token in keywords:
        for hint in hints.get(token, ()):
            if hint in normalized_line:
                score += 1
    return score


def build_view_one_payload(data_root: Path, source: str, job_id: str) -> ViewOnePayload:
    match_state = _read_json(
        data_root / source / job_id / "nodes" / "match" / "approved" / "state.json"
    )
    extract_state = _read_json(
        data_root
        / source
        / job_id
        / "nodes"
        / "extract_understand"
        / "approved"
        / "state.json"
    )

    requirements_map = {
        str(item.get("id", "")).strip(): str(item.get("text", "")).strip()
        for item in extract_state.get("requirements", [])
        if isinstance(item, dict)
    }

    nodes: list[GraphNode] = [
        GraphNode(id="profile", label="Profile", kind="profile"),
        GraphNode(id="job", label="Job Posting", kind="job"),
    ]
    edges: list[GraphEdge] = []

    for match in match_state.get("matches", []):
        if not isinstance(match, dict):
            continue
        req_id = str(match.get("req_id", "")).strip()
        if not req_id:
            continue
        label = req_id if req_id not in requirements_map else f"{req_id}"
        nodes.append(GraphNode(id=req_id, label=label, kind="requirement"))
        edges.append(
            GraphEdge(
                source="job",
                target=req_id,
                label="HAS_REQUIREMENT",
                score=None,
                reasoning=None,
                evidence_id=None,
            )
        )
        edges.append(
            GraphEdge(
                source=req_id,
                target="profile",
                label="MATCHED_BY",
                score=_as_float(match.get("match_score")),
                reasoning=str(match.get("reasoning", "") or ""),
                evidence_id=_as_text(match.get("evidence_id")),
            )
        )

    return ViewOnePayload(
        source=source,
        job_id=job_id,
        nodes=_dedupe_nodes(nodes),
        edges=edges,
    )


def build_view_three_payload(
    data_root: Path, source: str, job_id: str
) -> ViewThreePayload:
    job_root = data_root / source / job_id
    docs = {
        "cv": _read_text(
            job_root / "nodes" / "generate_documents" / "proposed" / "cv.md"
        ),
        "motivation_letter": _read_text(
            job_root
            / "nodes"
            / "generate_documents"
            / "proposed"
            / "motivation_letter.md"
        ),
        "application_email": _read_text(
            job_root
            / "nodes"
            / "generate_documents"
            / "proposed"
            / "application_email.md"
        ),
    }

    view_one = build_view_one_payload(data_root, source, job_id)
    return ViewThreePayload(
        source=source,
        job_id=job_id,
        documents=docs,
        nodes=view_one.nodes,
        edges=view_one.edges,
    )


def _as_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _dedupe_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    seen: set[str] = set()
    output: list[GraphNode] = []
    for node in nodes:
        if node.id in seen:
            continue
        seen.add(node.id)
        output.append(node)
    return output
