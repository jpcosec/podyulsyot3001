from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)

SAVED_GRAPH_FILENAME = "cv_profile_graph_saved.json"

from src.core.graph.state import build_thread_id
from src.interfaces.api.models import (
    CvDemonstratesEdge,
    CvDescription,
    CvEntry,
    CvGraphEdge,
    CvGraphNode,
    CvGraphPayload,
    CvProfileGraphPayload,
    CvSkill,
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


def build_base_cv_graph_payload(data_root: Path) -> CvGraphPayload:
    profile_path = (
        data_root.parent
        / "reference_data"
        / "profile"
        / "base_profile"
        / "profile_base_data.json"
    )
    profile_data = _read_json(profile_path)

    owner = profile_data.get("owner")
    if not isinstance(owner, dict):
        return CvGraphPayload(
            profile_id="profile:missing",
            snapshot_version="unknown",
            captured_on="unknown",
            nodes=[],
            edges=[],
        )

    full_name = str(owner.get("full_name", "Profile")).strip() or "Profile"
    profile_id = f"profile:{_slug(full_name)}"
    snapshot_version = str(profile_data.get("snapshot_version", "unknown"))
    captured_on = str(profile_data.get("captured_on", "unknown"))

    nodes: list[CvGraphNode] = []
    edges: list[CvGraphEdge] = []
    seen_skills: dict[str, str] = {}

    def add_node(
        node_id: str,
        label: str,
        node_type: str,
        depth: int,
        main_category: str,
        subcategory: str,
        source_path: str,
        source_index: int | None = None,
        meta: dict[str, str] | None = None,
    ) -> None:
        nodes.append(
            CvGraphNode(
                id=node_id,
                label=label,
                node_type=node_type,
                depth=depth,
                main_category=main_category,
                subcategory=subcategory,
                source_path=source_path,
                source_index=source_index,
                meta=meta or {},
            )
        )

    def add_edge(source_id: str, target_id: str, relation: str) -> None:
        edge_id = f"edge:{source_id}:{target_id}:{relation}"
        edges.append(
            CvGraphEdge(
                id=edge_id, source=source_id, target=target_id, relation=relation
            )
        )

    def add_skill(
        skill_name: str, source_id: str, source_path: str, source_index: int | None
    ) -> None:
        if not skill_name.strip():
            return
        canonical = _skill_key(skill_name)
        skill_id = seen_skills.get(canonical)
        if skill_id is None:
            skill_id = f"skill:{canonical}"
            seen_skills[canonical] = skill_id
            add_node(
                node_id=skill_id,
                label=skill_name.strip(),
                node_type="skill",
                depth=4,
                main_category="info",
                subcategory="skill",
                source_path=source_path,
                source_index=source_index,
            )
            add_edge("group:skills_pool", skill_id, "contains")
        add_edge(source_id, skill_id, "references_skill")

    add_node(
        node_id=profile_id,
        label=full_name,
        node_type="profile",
        depth=0,
        main_category="info",
        subcategory="profile",
        source_path="owner",
    )

    groups = [
        ("group:personal_data", "Personal Data", "personal_data"),
        ("group:experience", "Experience", "experience"),
        ("group:education", "Education", "education"),
        ("group:publications", "Publications", "publications"),
        ("group:relevant_experience", "Relevant Experience", "relevant_experience"),
        ("group:languages", "Languages", "languages"),
        ("group:skills_pool", "Skills Pool", "skills_pool"),
    ]
    for group_id, label, sub in groups:
        add_node(
            node_id=group_id,
            label=label,
            node_type="group",
            depth=1,
            main_category="info",
            subcategory=sub,
            source_path=sub,
        )
        add_edge(profile_id, group_id, "contains")

    add_node(
        node_id="owner:preferred_name",
        label=str(owner.get("preferred_name", "")).strip() or "Preferred Name",
        node_type="field",
        depth=2,
        main_category="info",
        subcategory="name",
        source_path="owner.preferred_name",
    )
    add_edge("group:personal_data", "owner:preferred_name", "contains")

    for key in ("birth_date", "nationality"):
        value = str(owner.get(key, "")).strip()
        if not value:
            continue
        node_id = f"owner:{key}"
        add_node(
            node_id=node_id,
            label=f"{key.replace('_', ' ').title()}: {value}",
            node_type="field",
            depth=2,
            main_category="info",
            subcategory=key,
            source_path=f"owner.{key}",
        )
        add_edge("group:personal_data", node_id, "contains")

    contact = owner.get("contact")
    if isinstance(contact, dict):
        email = str(contact.get("email", "")).strip()
        phone = str(contact.get("phone", "")).strip()
        if email:
            add_node(
                node_id="owner:contact:email",
                label=email,
                node_type="field",
                depth=2,
                main_category="info",
                subcategory="contact",
                source_path="owner.contact.email",
            )
            add_edge("group:personal_data", "owner:contact:email", "contains")
        if phone:
            add_node(
                node_id="owner:contact:phone",
                label=phone,
                node_type="field",
                depth=2,
                main_category="info",
                subcategory="contact",
                source_path="owner.contact.phone",
            )
            add_edge("group:personal_data", "owner:contact:phone", "contains")
        addresses = contact.get("addresses")
        if isinstance(addresses, list):
            for idx, address in enumerate(addresses):
                if not isinstance(address, dict):
                    continue
                label = str(address.get("label", "address")).strip() or "address"
                value = str(address.get("value", "")).strip()
                if not value:
                    continue
                node_id = f"owner:contact:address:{idx}"
                add_node(
                    node_id=node_id,
                    label=f"{label}: {value}",
                    node_type="field",
                    depth=2,
                    main_category="info",
                    subcategory="address",
                    source_path="owner.contact.addresses",
                    source_index=idx,
                )
                add_edge("group:personal_data", node_id, "contains")

    legal = owner.get("legal_status")
    if isinstance(legal, dict):
        for key in ("visa_type", "visa_status", "work_permission_germany"):
            if key not in legal:
                continue
            value = str(legal.get(key, "")).strip()
            if not value:
                continue
            node_id = f"owner:legal:{key}"
            add_node(
                node_id=node_id,
                label=f"{key.replace('_', ' ').title()}: {value}",
                node_type="field",
                depth=2,
                main_category="info",
                subcategory="legal_status",
                source_path=f"owner.legal_status.{key}",
            )
            add_edge("group:personal_data", node_id, "contains")

    education = profile_data.get("education")
    if isinstance(education, list):
        for idx, item in enumerate(education):
            if not isinstance(item, dict):
                continue
            degree = str(item.get("degree", "Education")).strip() or "Education"
            institution = str(item.get("institution", "")).strip()
            entry_id = f"edu:{idx}"
            entry_label = degree if not institution else f"{degree} @ {institution}"
            add_node(
                node_id=entry_id,
                label=entry_label,
                node_type="entry",
                depth=2,
                main_category="info",
                subcategory="education",
                source_path="education",
                source_index=idx,
            )
            add_edge("group:education", entry_id, "contains")
            for key in (
                "specialization",
                "location",
                "start_date",
                "end_date",
                "level_reference",
                "equivalency_note",
            ):
                value = str(item.get(key, "")).strip()
                if not value:
                    continue
                field_id = f"{entry_id}:field:{key}"
                add_node(
                    node_id=field_id,
                    label=f"{key.replace('_', ' ').title()}: {value}",
                    node_type="field",
                    depth=3,
                    main_category="info",
                    subcategory=key,
                    source_path=f"education[{idx}].{key}",
                )
                add_edge(entry_id, field_id, "contains")

    experience = profile_data.get("experience")
    if isinstance(experience, list):
        for idx, item in enumerate(experience):
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "Experience")).strip() or "Experience"
            organization = str(item.get("organization", "")).strip()
            entry_id = f"exp:{idx}"
            label = role if not organization else f"{role} @ {organization}"
            add_node(
                node_id=entry_id,
                label=label,
                node_type="entry",
                depth=2,
                main_category="info",
                subcategory="job_experience",
                source_path="experience",
                source_index=idx,
            )
            add_edge("group:experience", entry_id, "contains")

            for key in ("location", "start_date", "end_date"):
                value = str(item.get(key, "")).strip()
                if not value:
                    continue
                field_id = f"{entry_id}:field:{key}"
                add_node(
                    node_id=field_id,
                    label=f"{key.replace('_', ' ').title()}: {value}",
                    node_type="field",
                    depth=3,
                    main_category="info",
                    subcategory=key,
                    source_path=f"experience[{idx}].{key}",
                )
                add_edge(entry_id, field_id, "contains")

            achievements = item.get("achievements")
            if isinstance(achievements, list):
                for ach_idx, text in enumerate(achievements):
                    if not isinstance(text, str) or not text.strip():
                        continue
                    ach_id = f"{entry_id}:ach:{ach_idx}"
                    add_node(
                        node_id=ach_id,
                        label=short_text(text.strip(), 80),
                        node_type="bullet",
                        depth=3,
                        main_category="info",
                        subcategory="description",
                        source_path=f"experience[{idx}].achievements",
                        source_index=ach_idx,
                        meta={"full_text": text.strip()},
                    )
                    add_edge(entry_id, ach_id, "contains")

            keywords = item.get("keywords")
            if isinstance(keywords, list):
                for kw_idx, keyword in enumerate(keywords):
                    if not isinstance(keyword, str):
                        continue
                    add_skill(keyword, entry_id, f"experience[{idx}].keywords", kw_idx)

    publications = profile_data.get("publications")
    if isinstance(publications, list):
        for idx, item in enumerate(publications):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "Publication")).strip() or "Publication"
            entry_id = f"pub:{idx}"
            add_node(
                node_id=entry_id,
                label=title,
                node_type="entry",
                depth=2,
                main_category="info",
                subcategory="publication",
                source_path="publications",
                source_index=idx,
            )
            add_edge("group:publications", entry_id, "contains")
            for key in ("year", "venue", "url"):
                value = str(item.get(key, "")).strip()
                if not value:
                    continue
                field_id = f"{entry_id}:field:{key}"
                add_node(
                    node_id=field_id,
                    label=f"{key.title()}: {value}",
                    node_type="field",
                    depth=3,
                    main_category="info",
                    subcategory=key,
                    source_path=f"publications[{idx}].{key}",
                )
                add_edge(entry_id, field_id, "contains")

    projects = profile_data.get("projects")
    if isinstance(projects, list):
        for idx, item in enumerate(projects):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "Project")).strip() or "Project"
            role = str(item.get("role", "")).strip()
            entry_id = f"rel:{idx}"
            label = name if not role else f"{name} ({role})"
            add_node(
                node_id=entry_id,
                label=label,
                node_type="entry",
                depth=2,
                main_category="info",
                subcategory="relevant_experience",
                source_path="projects",
                source_index=idx,
            )
            add_edge("group:relevant_experience", entry_id, "contains")
            stack = item.get("stack")
            if isinstance(stack, list):
                for sk_idx, skill in enumerate(stack):
                    if not isinstance(skill, str):
                        continue
                    add_skill(skill, entry_id, f"projects[{idx}].stack", sk_idx)

    languages = profile_data.get("languages")
    if isinstance(languages, list):
        for idx, item in enumerate(languages):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "Language")).strip() or "Language"
            level = str(item.get("level", "")).strip()
            entry_id = f"lang:{_slug(name)}"
            label = name if not level else f"{name} ({level})"
            add_node(
                node_id=entry_id,
                label=label,
                node_type="entry",
                depth=2,
                main_category="info",
                subcategory="language",
                source_path="languages",
                source_index=idx,
            )
            add_edge("group:languages", entry_id, "contains")
            note = str(item.get("note", "")).strip()
            if note:
                note_id = f"{entry_id}:note"
                add_node(
                    node_id=note_id,
                    label=note,
                    node_type="field",
                    depth=3,
                    main_category="info",
                    subcategory="language_note",
                    source_path=f"languages[{idx}].note",
                )
                add_edge(entry_id, note_id, "contains")

    skills = profile_data.get("skills")
    if isinstance(skills, dict):
        for category, items in skills.items():
            if not isinstance(items, list):
                continue
            for idx, item in enumerate(items):
                if not isinstance(item, str):
                    continue
                canonical = _skill_key(item)
                skill_id = seen_skills.get(canonical)
                if skill_id is None:
                    skill_id = f"skill:{canonical}"
                    seen_skills[canonical] = skill_id
                    add_node(
                        node_id=skill_id,
                        label=item.strip(),
                        node_type="skill",
                        depth=4,
                        main_category="info",
                        subcategory="skill",
                        source_path=f"skills.{category}",
                        source_index=idx,
                        meta={"skill_category": category},
                    )
                    add_edge("group:skills_pool", skill_id, "contains")

    return CvGraphPayload(
        profile_id=profile_id,
        snapshot_version=snapshot_version,
        captured_on=captured_on,
        nodes=nodes,
        edges=edges,
    )


def _profile_dir(data_root: Path) -> Path:
    return data_root.parent / "reference_data" / "profile" / "base_profile"


def _saved_graph_path(data_root: Path) -> Path:
    return _profile_dir(data_root) / SAVED_GRAPH_FILENAME


def _deserialize_cv_profile_graph(raw: dict) -> CvProfileGraphPayload:
    entries = [
        CvEntry(
            id=entry["id"],
            category=entry["category"],
            essential=bool(entry.get("essential", False)),
            fields=dict(entry.get("fields", {})),
            descriptions=[
                CvDescription(
                    key=desc["key"],
                    text=desc["text"],
                    weight=desc.get("weight", "primary_detail"),
                )
                for desc in entry.get("descriptions", [])
            ],
        )
        for entry in raw.get("entries", [])
    ]
    skills = [
        CvSkill(
            id=skill["id"],
            label=skill["label"],
            category=skill.get("category", "uncategorized"),
            essential=bool(skill.get("essential", False)),
            level=skill.get("level"),
            meta=dict(skill.get("meta", {})),
        )
        for skill in raw.get("skills", [])
    ]
    demonstrates = [
        CvDemonstratesEdge(
            id=edge["id"],
            source=edge["source"],
            target=edge["target"],
            description_keys=list(edge.get("description_keys", [])),
        )
        for edge in raw.get("demonstrates", [])
    ]
    return CvProfileGraphPayload(
        profile_id=raw["profile_id"],
        snapshot_version=raw.get("snapshot_version", "unknown"),
        captured_on=raw.get("captured_on", "unknown"),
        entries=entries,
        skills=skills,
        demonstrates=demonstrates,
    )


def _load_saved_cv_profile_graph(
    data_root: Path,
) -> CvProfileGraphPayload | None:
    path = _saved_graph_path(data_root)
    raw = _read_json(path)
    if not raw:
        return None
    try:
        return _deserialize_cv_profile_graph(raw)
    except (KeyError, TypeError, ValueError):
        logger.warning("Corrupted saved graph at %s — rebuilding from profile", path)
        return None


def save_cv_profile_graph_payload(
    data_root: Path,
    payload: CvProfileGraphPayload,
) -> Path:
    path = _saved_graph_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_cv_profile_graph_payload(data_root: Path) -> CvProfileGraphPayload:
    saved = _load_saved_cv_profile_graph(data_root)
    if saved is not None:
        return saved
    return _build_cv_profile_graph_from_base(data_root)


def build_cv_profile_graph_payload(data_root: Path) -> CvProfileGraphPayload:
    return load_cv_profile_graph_payload(data_root)


def _build_cv_profile_graph_from_base(data_root: Path) -> CvProfileGraphPayload:
    profile_path = _profile_dir(data_root) / "profile_base_data.json"
    profile_data = _read_json(profile_path)
    owner = profile_data.get("owner")
    if not isinstance(owner, dict):
        return CvProfileGraphPayload(
            profile_id="profile:missing",
            snapshot_version="unknown",
            captured_on="unknown",
            entries=[],
            skills=[],
            demonstrates=[],
        )

    full_name = str(owner.get("full_name", "Profile")).strip() or "Profile"
    profile_id = f"profile:{_slug(full_name)}"
    snapshot_version = str(profile_data.get("snapshot_version", "unknown"))
    captured_on = str(profile_data.get("captured_on", "unknown"))

    entries: list[CvEntry] = []
    skills_by_id: dict[str, CvSkill] = {}
    demonstrates_by_id: dict[str, CvDemonstratesEdge] = {}
    used_entry_ids: set[str] = set()

    def add_entry(
        *,
        category: str,
        essential: bool,
        fields: dict[str, object],
        descriptions_source: list[object] | None,
        id_hint: str,
    ) -> tuple[str, list[CvDescription]]:
        entry_id = _unique_id(f"entry:{category}", id_hint, used_entry_ids)
        descriptions = _build_descriptions(descriptions_source or [])
        entries.append(
            CvEntry(
                id=entry_id,
                category=category,
                essential=essential,
                fields=fields,
                descriptions=descriptions,
            )
        )
        return entry_id, descriptions

    def add_skill(
        label: str,
        *,
        category: str,
        essential: bool = False,
        level: str | None = None,
        meta: dict[str, object] | None = None,
    ) -> str:
        if not label.strip():
            return ""
        skill_id = f"skill:{_skill_key(label)}"
        previous = skills_by_id.get(skill_id)
        if previous is None:
            skills_by_id[skill_id] = CvSkill(
                id=skill_id,
                label=label.strip(),
                category=category,
                essential=essential,
                level=level,
                meta=meta or {},
            )
            return skill_id

        merged_meta = dict(previous.meta)
        if meta:
            merged_meta.update(meta)
        merged_category = (
            previous.category if previous.category != "uncategorized" else category
        )
        merged_level = previous.level or level
        skills_by_id[skill_id] = CvSkill(
            id=previous.id,
            label=previous.label,
            category=merged_category,
            essential=previous.essential or essential,
            level=merged_level,
            meta=merged_meta,
        )
        return skill_id

    def add_demonstrates(
        entry_id: str,
        skill_id: str,
        description_keys: list[str],
    ) -> None:
        if not entry_id or not skill_id:
            return
        edge_id = f"edge:{entry_id}:demonstrates:{skill_id}"
        current = demonstrates_by_id.get(edge_id)
        if current is None:
            demonstrates_by_id[edge_id] = CvDemonstratesEdge(
                id=edge_id,
                source=entry_id,
                target=skill_id,
                description_keys=sorted(set(description_keys)),
            )
            return
        merged = sorted(set(current.description_keys) | set(description_keys))
        demonstrates_by_id[edge_id] = CvDemonstratesEdge(
            id=current.id,
            source=current.source,
            target=current.target,
            description_keys=merged,
        )

    raw_skills = profile_data.get("skills")
    skill_category_by_key: dict[str, str] = {}
    skill_label_by_key: dict[str, str] = {}
    if isinstance(raw_skills, dict):
        for raw_category, values in raw_skills.items():
            if not isinstance(values, list):
                continue
            category = _normalize_skill_category(raw_category)
            for item in values:
                if not isinstance(item, str):
                    continue
                key = _skill_key(item)
                skill_category_by_key[key] = category
                skill_label_by_key.setdefault(key, item.strip())
                add_skill(
                    item,
                    category=category,
                    essential=False,
                    meta={"source": f"skills.{raw_category}"},
                )

    personal_fields: dict[str, object] = {}
    for key in ("full_name", "preferred_name", "birth_date", "nationality"):
        value = owner.get(key)
        if isinstance(value, str) and value.strip():
            personal_fields[key] = value.strip()
    if personal_fields:
        add_entry(
            category="personal_data",
            essential=True,
            fields=personal_fields,
            descriptions_source=[],
            id_hint=str(personal_fields.get("preferred_name", full_name)),
        )

    contact = owner.get("contact")
    links = owner.get("links")
    contact_fields: dict[str, object] = {}
    if isinstance(contact, dict):
        for key in ("email", "phone"):
            value = contact.get(key)
            if isinstance(value, str) and value.strip():
                contact_fields[key] = value.strip()
        addresses = contact.get("addresses")
        if isinstance(addresses, list):
            normalized_addresses: list[dict[str, str]] = []
            for item in addresses:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label", "")).strip()
                value = str(item.get("value", "")).strip()
                if not value:
                    continue
                normalized_addresses.append({"label": label, "value": value})
            if normalized_addresses:
                contact_fields["addresses"] = normalized_addresses
    if isinstance(links, dict):
        normalized_links: dict[str, str] = {}
        for key, value in links.items():
            if isinstance(value, str) and value.strip():
                normalized_links[key] = value.strip()
        if normalized_links:
            contact_fields["links"] = normalized_links
    if contact_fields:
        add_entry(
            category="contact",
            essential=True,
            fields=contact_fields,
            descriptions_source=[],
            id_hint="contact",
        )

    legal = owner.get("legal_status")
    if isinstance(legal, dict):
        legal_fields: dict[str, object] = {}
        for key in ("visa_type", "visa_status", "work_permission_germany"):
            if key not in legal:
                continue
            value = legal.get(key)
            if isinstance(value, str) and value.strip():
                legal_fields[key] = value.strip()
            elif isinstance(value, bool):
                legal_fields[key] = value
        if legal_fields:
            add_entry(
                category="legal_status",
                essential=True,
                fields=legal_fields,
                descriptions_source=[],
                id_hint="legal_status",
            )

    education = profile_data.get("education")
    if isinstance(education, list):
        for idx, item in enumerate(education):
            if not isinstance(item, dict):
                continue
            fields: dict[str, object] = {}
            for key in (
                "degree",
                "specialization",
                "institution",
                "location",
                "start_date",
                "end_date",
                "level_reference",
                "equivalency_note",
            ):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    fields[key] = value.strip()
            if not fields:
                continue
            add_entry(
                category="education",
                essential=False,
                fields=fields,
                descriptions_source=[],
                id_hint=f"{idx}_{fields.get('degree', 'education')}",
            )

    experience = profile_data.get("experience")
    if isinstance(experience, list):
        for idx, item in enumerate(experience):
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip()
            category = "internship" if "intern" in role.lower() else "job_experience"
            fields: dict[str, object] = {}
            for key in ("role", "organization", "location", "start_date", "end_date"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    fields[key] = value.strip()
            descriptions_source: list[object] = []
            achievements = item.get("achievements")
            if isinstance(achievements, list):
                descriptions_source = [
                    value for value in achievements if isinstance(value, str)
                ]
            entry_id, descriptions = add_entry(
                category=category,
                essential=False,
                fields=fields,
                descriptions_source=descriptions_source,
                id_hint=f"{idx}_{role}_{fields.get('organization', '')}",
            )

            keywords = item.get("keywords")
            if isinstance(keywords, list):
                for keyword in keywords:
                    if not isinstance(keyword, str) or not keyword.strip():
                        continue
                    skill_key = _skill_key(keyword)
                    skill_category = skill_category_by_key.get(
                        skill_key, "uncategorized"
                    )
                    skill_id = add_skill(
                        keyword,
                        category=skill_category,
                        essential=False,
                        meta={"source": f"experience[{idx}].keywords"},
                    )
                    keys = _matching_description_keys(descriptions, keyword)
                    if not keys:
                        keys = [desc.key for desc in descriptions]
                    add_demonstrates(entry_id, skill_id, keys)

            for known_key, known_category in skill_category_by_key.items():
                known_label = skill_label_by_key.get(
                    known_key, known_key.replace("_", " ")
                )
                matched_keys = _matching_description_keys(descriptions, known_label)
                if not matched_keys:
                    continue
                skill_id = add_skill(
                    known_label,
                    category=known_category,
                    essential=False,
                    meta={"source": "description_extraction"},
                )
                add_demonstrates(entry_id, skill_id, matched_keys)

    publications = profile_data.get("publications")
    if isinstance(publications, list):
        for idx, item in enumerate(publications):
            if not isinstance(item, dict):
                continue
            fields: dict[str, object] = {}
            for key in ("title", "year", "venue", "url"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    fields[key] = value.strip()
                elif isinstance(value, int):
                    fields[key] = value
            if not fields:
                continue
            add_entry(
                category="publication",
                essential=False,
                fields=fields,
                descriptions_source=[],
                id_hint=f"{idx}_{fields.get('title', 'publication')}",
            )

    projects = profile_data.get("projects")
    if isinstance(projects, list):
        for idx, item in enumerate(projects):
            if not isinstance(item, dict):
                continue
            fields: dict[str, object] = {}
            for key in ("name", "role"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    fields[key] = value.strip()
            entry_id, descriptions = add_entry(
                category="project",
                essential=False,
                fields=fields,
                descriptions_source=[],
                id_hint=f"{idx}_{fields.get('name', 'project')}",
            )
            stack = item.get("stack")
            if isinstance(stack, list):
                for skill in stack:
                    if not isinstance(skill, str) or not skill.strip():
                        continue
                    skill_key = _skill_key(skill)
                    skill_category = skill_category_by_key.get(
                        skill_key, "uncategorized"
                    )
                    skill_id = add_skill(
                        skill,
                        category=skill_category,
                        essential=False,
                        meta={"source": f"projects[{idx}].stack"},
                    )
                    add_demonstrates(
                        entry_id, skill_id, [desc.key for desc in descriptions]
                    )

    languages = profile_data.get("languages")
    if isinstance(languages, list):
        for idx, item in enumerate(languages):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            level = str(item.get("level", "")).strip() or None
            note = str(item.get("note", "")).strip()
            if not name:
                continue
            fields: dict[str, object] = {"name": name}
            if level:
                fields["level"] = level
            if note:
                fields["note"] = note
            descriptions_source: list[object] = []
            if note:
                descriptions_source.append(note)
            if level:
                descriptions_source.append(f"{name} proficiency {level}")
            entry_id, descriptions = add_entry(
                category="language_fact",
                essential=False,
                fields=fields,
                descriptions_source=descriptions_source,
                id_hint=f"{idx}_{name}",
            )
            skill_id = add_skill(
                name,
                category="language",
                essential=False,
                level=level,
                meta={"source": "languages"},
            )
            add_demonstrates(entry_id, skill_id, [desc.key for desc in descriptions])

    skills = sorted(skills_by_id.values(), key=lambda item: item.id)
    demonstrates = sorted(demonstrates_by_id.values(), key=lambda item: item.id)

    return CvProfileGraphPayload(
        profile_id=profile_id,
        snapshot_version=snapshot_version,
        captured_on=captured_on,
        entries=entries,
        skills=skills,
        demonstrates=demonstrates,
    )


def _build_descriptions(values: list[object]) -> list[CvDescription]:
    descriptions: list[CvDescription] = []
    used_keys: set[str] = set()
    for value in values:
        text = ""
        weight = "primary_detail"
        if isinstance(value, str):
            text = value.strip()
        elif isinstance(value, dict):
            raw_text = value.get("text")
            raw_weight = value.get("weight")
            if isinstance(raw_text, str):
                text = raw_text.strip()
            if isinstance(raw_weight, str) and raw_weight.strip():
                weight = raw_weight.strip()
        if not text:
            continue
        key = _unique_slug(text, used_keys)
        descriptions.append(CvDescription(key=key, text=text, weight=weight))
    return descriptions


def _unique_id(prefix: str, value: str, used: set[str]) -> str:
    base = _slug(value)
    candidate = f"{prefix}:{base}"
    if candidate not in used:
        used.add(candidate)
        return candidate
    suffix = 2
    while True:
        next_candidate = f"{candidate}_{suffix}"
        if next_candidate not in used:
            used.add(next_candidate)
            return next_candidate
        suffix += 1


def _unique_slug(value: str, used: set[str]) -> str:
    base = _slug(value)
    if base not in used:
        used.add(base)
        return base
    suffix = 2
    while True:
        candidate = f"{base}_{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        suffix += 1


def _matching_description_keys(
    descriptions: list[CvDescription],
    token: str,
) -> list[str]:
    needle = token.strip().lower()
    if not needle:
        return []
    is_word_like = bool(re.fullmatch(r"[a-z0-9_\-]+", needle))
    pattern: re.Pattern[str] | None = None
    if is_word_like:
        pattern = re.compile(rf"\b{re.escape(needle)}\b", re.IGNORECASE)
    output: list[str] = []
    for description in descriptions:
        if is_word_like and pattern is not None:
            if pattern.search(description.text):
                output.append(description.key)
        elif needle in description.text.lower():
            output.append(description.key)
    return output


def _normalize_skill_category(value: str) -> str:
    mapping = {
        "programming_languages": "programming",
        "ml_ai": "machine_learning",
        "data_platforms": "data_platform",
        "orchestration_devops": "devops",
        "electronics_robotics": "electronics_robotics",
    }
    return mapping.get(value, _slug(value))


def _skill_key(value: str) -> str:
    return _slug(value)


def _slug(value: str) -> str:
    output = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return output or "item"


def short_text(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return f"{value[: max_len - 3]}..."
