"""Matching node logic: requirements vs profile evidence."""

from __future__ import annotations

import os
from typing import Any, Mapping

from src.ai.prompt_manager import PromptManager
from src.ai.runtime import LLMRuntime
from src.core.io import (
    ArtifactWriter,
    ObservabilityService,
    ProvenanceService,
    WorkspaceManager,
)
from src.core.round_manager import RoundManager
from src.nodes.match.contract import MatchEnvelope


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Generate structured requirement/evidence match assessment."""
    input_data = _build_input_data(state)

    prompt_manager = PromptManager(base_path="src/nodes")
    model_name = os.getenv("PHD2_GEMINI_MODEL", "gemini-2.5-flash")
    runtime = LLMRuntime(model_name=model_name)

    system_prompt, user_prompt = prompt_manager.build_prompt(
        "match",
        input_data,
        required_xml_tags=("job_requirements", "profile_evidence"),
        optional_xml_tags=("round_feedback", "regeneration_scope"),
    )

    match_result = runtime.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_schema=MatchEnvelope,
    )

    matched_payload = match_result.model_dump()
    _persist_match_artifacts(state, matched_payload, input_data)

    next_status = "pending_review" if _has_job_scope(state) else "running"

    result = {
        **dict(state),
        "current_node": "match",
        "status": next_status,
        "pending_gate": "review_match"
        if next_status == "pending_review"
        else state.get("pending_gate"),
        "matched_data": matched_payload,
    }
    _write_execution_metadata("match", result)
    return result


def _build_input_data(state: Mapping[str, Any]) -> dict[str, Any]:
    job_id = state.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("state.job_id is required")

    extracted = state.get("extracted_data")
    requirements = (
        extracted.get("requirements") if isinstance(extracted, Mapping) else None
    )
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("state.extracted_data.requirements is required")

    profile_evidence_raw = state.get("my_profile_evidence")
    if not isinstance(profile_evidence_raw, list) or not profile_evidence_raw:
        raise ValueError("state.my_profile_evidence is required")

    profile_evidence = _load_effective_evidence(state, profile_evidence_raw)
    out = {
        "job_id": job_id,
        "requirements": requirements,
        "profile_evidence": profile_evidence,
        "prev_round": None,
        "round_feedback": None,
        "regeneration_scope": None,
    }

    feedback_context = _load_regeneration_feedback(state)
    if feedback_context is not None:
        out["prev_round"] = feedback_context["prev_round"]
        out["round_feedback"] = feedback_context["feedback"]
        out["regeneration_scope"] = _collect_regeneration_scope(
            feedback_context["feedback"]
        )

    return out


def _collect_regeneration_scope(round_feedback: Any) -> list[str]:
    if not isinstance(round_feedback, list):
        return []

    scope: list[str] = []
    seen: set[str] = set()
    for item in round_feedback:
        if not isinstance(item, Mapping):
            continue
        req_id = str(item.get("req_id", "")).strip()
        action = str(item.get("action", "")).strip().lower()
        if action != "patch" or not req_id or req_id in seen:
            continue
        scope.append(req_id)
        seen.add(req_id)
    return scope


def _load_effective_evidence(
    state: Mapping[str, Any],
    base_profile_evidence: list[Any],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = [
        dict(item) for item in base_profile_evidence if isinstance(item, Mapping)
    ]
    if not _has_job_scope(state):
        return evidence

    manager = _round_manager_for_state(state)
    patches = manager.get_all_feedback_patches()
    if not patches:
        return evidence

    seen_ids = {
        str(item.get("id", "")).strip()
        for item in evidence
        if str(item.get("id", "")).strip()
    }
    for patch in patches:
        patch_id = str(patch.get("id", "")).strip()
        description = str(patch.get("description", "")).strip()
        if not patch_id or not description or patch_id in seen_ids:
            continue
        evidence.append({"id": patch_id, "description": description})
        seen_ids.add(patch_id)

    return evidence


def _load_regeneration_feedback(
    state: Mapping[str, Any],
) -> dict[str, Any] | None:
    if state.get("review_decision") != "request_regeneration":
        return None

    if not _has_job_scope(state):
        raise ValueError("request_regeneration requires state.source and state.job_id")

    manager = _round_manager_for_state(state)
    feedback_payload = manager.get_latest_feedback()
    if not isinstance(feedback_payload, Mapping):
        raise ValueError(
            "request_regeneration requires review/rounds/<latest>/feedback.json"
        )

    prev_round = feedback_payload.get("round_n")
    if not isinstance(prev_round, int) or prev_round < 1:
        raise ValueError("feedback.json must contain integer field round_n >= 1")

    items = feedback_payload.get("feedback")
    if not isinstance(items, list) or not items:
        raise ValueError("feedback.json must contain non-empty feedback list")

    normalized: list[dict[str, Any]] = []
    patch_actions = 0
    for item in items:
        if not isinstance(item, Mapping):
            continue
        req_id = str(item.get("req_id", "")).strip()
        action = str(item.get("action", "")).strip().lower()
        reviewer_note = str(item.get("reviewer_note", "")).strip()
        if not req_id or not action:
            continue

        patch_evidence = item.get("patch_evidence")
        normalized_patch = None
        if isinstance(patch_evidence, Mapping):
            patch_id = str(patch_evidence.get("id", "")).strip()
            description = str(patch_evidence.get("description", "")).strip()
            if patch_id and description:
                normalized_patch = {"id": patch_id, "description": description}

        if action == "patch" or normalized_patch is not None:
            patch_actions += 1

        normalized.append(
            {
                "req_id": req_id,
                "action": action,
                "reviewer_note": reviewer_note,
                "patch_evidence": normalized_patch,
            }
        )

    if not normalized:
        raise ValueError("feedback.json feedback list has no valid entries")
    if patch_actions < 1:
        raise ValueError(
            "request_regeneration requires at least one actionable patch entry"
        )

    return {"prev_round": prev_round, "feedback": normalized}


def _has_job_scope(state: Mapping[str, Any]) -> bool:
    source = state.get("source")
    job_id = state.get("job_id")
    return (
        isinstance(source, str)
        and bool(source.strip())
        and isinstance(job_id, str)
        and bool(job_id.strip())
    )


def _persist_match_artifacts(
    state: Mapping[str, Any],
    matched_data: dict[str, Any],
    input_data: Mapping[str, Any],
) -> None:
    if not _has_job_scope(state):
        return

    source = str(state["source"]).strip()
    job_id = str(state["job_id"]).strip()
    workspace = WorkspaceManager()
    writer = ArtifactWriter(workspace)
    job_root = workspace.job_root(source, job_id)

    proposed_path = writer.write_node_stage_json(
        source=source,
        job_id=job_id,
        node_name="match",
        stage="approved",
        filename="state.json",
        payload=matched_data,
    )
    source_hash = ProvenanceService.sha256_file(proposed_path)

    manager = RoundManager(job_root)
    round_number = manager.create_next_round()

    render_payload = {
        **matched_data,
        "job_id": state.get("job_id"),
        "requirements": input_data.get("requirements", []),
        "profile_evidence": input_data.get("profile_evidence", []),
    }
    rendered = _render_decision_markdown(
        render_payload,
        round_number,
        source_hash=source_hash,
        prev_round=input_data.get("prev_round"),
        round_feedback=input_data.get("round_feedback"),
    )
    round_md_path = manager.save_artifact(round_number, "decision.md", rendered)
    active_md_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="match",
        stage="review",
        filename="decision.md",
    )
    writer.write_text(active_md_path, round_md_path.read_text(encoding="utf-8"))


def _render_decision_markdown(
    matched_data: Mapping[str, Any],
    round_number: int,
    *,
    source_hash: str,
    prev_round: Any,
    round_feedback: Any,
) -> str:
    requirement_lookup = _build_requirement_lookup(matched_data)
    evidence_lookup = _build_evidence_lookup(matched_data)
    regeneration_scope = _collect_regeneration_scope(round_feedback)
    review_matches, context_matches = _split_matches_for_review_scope(
        matched_data,
        regeneration_scope,
    )

    lines = [
        "---",
        f'source_state_hash: "{source_hash}"',
        'node: "match"',
        f'job_id: "{matched_data.get("job_id", "")}"',
        f"round: {round_number}",
        "---",
        "",
        "# Match Review",
        f"Round: {round_number}",
        "",
    ]

    if (
        isinstance(prev_round, int)
        and isinstance(round_feedback, list)
        and round_feedback
    ):
        lines.extend(
            [
                f"## Feedback Applied from Round {prev_round}",
                "",
            ]
        )
        for item in round_feedback:
            if not isinstance(item, Mapping):
                continue
            req_id = str(item.get("req_id", "")).strip()
            action = str(item.get("action", "")).strip()
            note = str(item.get("reviewer_note", "")).strip()
            if req_id:
                lines.append(f"- [{req_id}] ({action}) {note}".strip())
        lines.append("")

    if regeneration_scope and context_matches:
        lines.extend(
            [
                "## Context (Outside Regeneration Scope)",
                "",
                "Rows below are kept for visibility and do not require revalidation in this round.",
                "",
                "| Req ID | Requirement | Evidence (from profile) | Score | Reasoning | Status |",
                "|---|---|---|---:|---|---|",
            ]
        )
        for item in context_matches:
            if not isinstance(item, Mapping):
                continue
            req_id = _md_cell(str(item.get("req_id", "")))
            requirement_text = _md_cell(
                requirement_lookup.get(
                    str(item.get("req_id", "")), "(requirement text unavailable)"
                )
            )
            evidence_id = str(item.get("evidence_id") or "-")
            evidence_text = _md_cell(
                _render_evidence_text(evidence_id, evidence_lookup)
            )
            score_val = _safe_score(item.get("match_score"))
            reasoning = _md_cell(
                str(item.get("reasoning", "")).replace("\n", " ").strip()
            )
            lines.append(
                f"| {req_id} | {requirement_text} | {evidence_text} | {score_val:.2f} | {reasoning} | carried forward |"
            )
        lines.append("")

    if regeneration_scope:
        lines.extend(
            [
                "## Regeneration Scope (Action Required)",
                "",
                "Only the rows in this section enter the revalidation loop.",
                "",
            ]
        )

    lines.extend(
        [
            "| Req ID | Requirement | Evidence (from profile) | Score | Reasoning | Action | Comments |",
            "|---|---|---|---:|---|---|---|",
        ]
    )

    for item in review_matches:
        if not isinstance(item, Mapping):
            continue
        req_id_raw = str(item.get("req_id", ""))
        req_id = _md_cell(req_id_raw)
        requirement_text = requirement_lookup.get(
            req_id_raw, "(requirement text unavailable)"
        )
        evidence_id = str(item.get("evidence_id") or "-")
        evidence_text = _render_evidence_text(evidence_id, evidence_lookup)
        score_val = _safe_score(item.get("match_score"))
        reasoning = _md_cell(str(item.get("reasoning", "")).replace("\n", " ").strip())
        requirement_text = _md_cell(requirement_text)
        evidence_text = _md_cell(evidence_text)
        lines.append(
            f"| {req_id} | {requirement_text} | {evidence_text} | {score_val:.2f} | {reasoning} | [ ] Proceed / [ ] Regen / [ ] Reject | - |"
        )

    return "\n".join(lines)


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").strip()


def _safe_score(raw: Any) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _split_matches_for_review_scope(
    matched_data: Mapping[str, Any],
    regeneration_scope: list[str],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    all_matches = [
        item for item in matched_data.get("matches", []) if isinstance(item, Mapping)
    ]
    if not regeneration_scope:
        return all_matches, []

    match_by_req_id: dict[str, Mapping[str, Any]] = {}
    for item in all_matches:
        req_id = str(item.get("req_id", "")).strip()
        if req_id and req_id not in match_by_req_id:
            match_by_req_id[req_id] = item

    scope_set = set(regeneration_scope)
    review_matches: list[Mapping[str, Any]] = []
    for req_id in regeneration_scope:
        scoped_match = match_by_req_id.get(req_id)
        if scoped_match is not None:
            review_matches.append(scoped_match)
            continue
        review_matches.append(
            {
                "req_id": req_id,
                "evidence_id": "-",
                "match_score": 0.0,
                "reasoning": "Requested regeneration item is missing from the latest model output.",
            }
        )

    context_matches = [
        item
        for item in all_matches
        if str(item.get("req_id", "")).strip() not in scope_set
    ]
    return review_matches, context_matches


def _round_manager_for_state(state: Mapping[str, Any]) -> RoundManager:
    source = str(state["source"]).strip()
    job_id = str(state["job_id"]).strip()
    workspace = WorkspaceManager()
    job_root = workspace.job_root(source, job_id)
    return RoundManager(job_root)


def _build_requirement_lookup(matched_data: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    requirements = matched_data.get("requirements")
    if not isinstance(requirements, list):
        return out

    for req in requirements:
        if not isinstance(req, Mapping):
            continue
        req_id = str(req.get("id", "")).strip()
        text = str(req.get("text", "")).replace("\n", " ").strip()
        if req_id and text:
            out[req_id] = text
    return out


def _build_evidence_lookup(matched_data: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    profile = matched_data.get("profile_evidence")
    if not isinstance(profile, list):
        return out

    for item in profile:
        if not isinstance(item, Mapping):
            continue
        evidence_id = str(item.get("id", "")).strip()
        description = str(item.get("description", "")).replace("\n", " ").strip()
        if evidence_id and description:
            out[evidence_id] = description
    return out


def _render_evidence_text(evidence_id: str, evidence_lookup: Mapping[str, str]) -> str:
    if evidence_id == "-":
        return "-"

    parts = [part.strip() for part in evidence_id.split(",") if part.strip()]
    if not parts:
        return "-"

    descriptions = [
        evidence_lookup.get(pid, "(description unavailable)") for pid in parts
    ]
    return " ; ".join(descriptions)


def _write_execution_metadata(node_name: str, state: Mapping[str, Any]) -> None:
    workspace = WorkspaceManager()
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)
    service.write_node_execution_snapshot(node_name=node_name, state=state)
