"""Review surface generation and deterministic decision parsing for match."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, cast

from src.core.io import (
    ArtifactReader,
    ArtifactWriter,
    ObservabilityService,
    WorkspaceManager,
)
from src.core.tools.review_decision_service import (
    feedback_action_from_decision,
    parse_checkbox_decision,
    route_from_decision_values,
    validate_feedback_payload_for_route,
)
from src.core.round_manager import RoundManager
from src.nodes.review_match.contract import DecisionEnvelope, ParsedDecision


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Ensure review markdown exists and parse decision when provided."""
    source, job_id, matched_data = _require_review_inputs(state)
    workspace = WorkspaceManager()
    reader = ArtifactReader(workspace)
    writer = ArtifactWriter(workspace)
    job_root = workspace.job_root(source, job_id)
    manager = RoundManager(job_root)
    review_dir = manager.review_dir
    review_dir.mkdir(parents=True, exist_ok=True)

    proposed_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="match",
        stage="approved",
        filename="state.json",
    )
    proposed_ref = str(proposed_path.relative_to(job_root))
    source_hash = _compute_source_hash(matched_data, proposed_path)

    decision_md_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="match",
        stage="review",
        filename="decision.md",
    )
    decision_json_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="match",
        stage="review",
        filename="decision.json",
    )

    if not decision_md_path.exists():
        fallback_round = manager.get_latest_round() or manager.create_next_round()
        extracted = state.get("extracted_data")
        requirements = (
            extracted.get("requirements")
            if isinstance(extracted, Mapping)
            and isinstance(extracted.get("requirements"), list)
            else []
        )
        profile = _effective_profile_evidence(state, manager)

        render_payload = {
            **dict(matched_data),
            "requirements": requirements,
            "profile_evidence": profile,
        }
        rendered = _render_decision_md(
            job_id,
            render_payload,
            source_hash,
            round_number=fallback_round,
        )
        manager.save_artifact(fallback_round, "decision.md", rendered)
        writer.write_text(decision_md_path, rendered)
        result = {
            **dict(state),
            "current_node": "review_match",
            "status": "pending_review",
            "pending_gate": "review_match",
            "review_decision": None,
            "artifact_refs": {
                **dict(state.get("artifact_refs") or {}),
                "last_decision_ref": str(decision_md_path.relative_to(job_root)),
            },
        }
        _write_execution_metadata("review_match", result)
        return result

    decision_text = reader.read_text(decision_md_path)
    round_number = _extract_round_number_from_text(decision_text)
    if round_number is None:
        round_number = manager.get_latest_round() or 1

    expected_hash = source_hash
    embedded_hash = _extract_source_hash_from_text(decision_text)
    if embedded_hash is None:
        if _has_any_checked_decision(decision_text):
            raise ValueError(
                "decision.md is missing source_state_hash; regenerate review markdown "
                "from current nodes/match/approved/state.json and re-apply decisions"
            )
        extracted = state.get("extracted_data")
        requirements = (
            extracted.get("requirements")
            if isinstance(extracted, Mapping)
            and isinstance(extracted.get("requirements"), list)
            else []
        )
        profile = _effective_profile_evidence(state, manager)
        render_payload = {
            **dict(matched_data),
            "requirements": requirements,
            "profile_evidence": profile,
        }
        rendered = _render_decision_md(
            job_id,
            render_payload,
            expected_hash,
            round_number=round_number,
        )
        manager.save_artifact(round_number, "decision.md", rendered)
        writer.write_text(decision_md_path, rendered)
        result = {
            **dict(state),
            "current_node": "review_match",
            "status": "pending_review",
            "pending_gate": "review_match",
            "review_decision": None,
            "artifact_refs": {
                **dict(state.get("artifact_refs") or {}),
                "last_decision_ref": str(decision_md_path.relative_to(job_root)),
            },
        }
        _write_execution_metadata("review_match", result)
        return result

    if embedded_hash != expected_hash:
        raise ValueError(
            "decision.md source_state_hash mismatch; regenerate review markdown "
            "from current nodes/match/approved/state.json before resuming"
        )

    parsed_decisions, routing_decision = _parse_decision_markdown(
        decision_text,
        matched_data,
    )
    if parsed_decisions is None or routing_decision is None:
        result = {
            **dict(state),
            "current_node": "review_match",
            "status": "pending_review",
            "pending_gate": "review_match",
            "review_decision": None,
        }
        _write_execution_metadata("review_match", result)
        return result

    envelope = DecisionEnvelope(
        node="review_match",
        job_id=job_id,
        round=round_number,
        source_state_hash=source_hash,
        decisions=parsed_decisions,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    manager.save_artifact(round_number, "decision.md", decision_text)
    manager.save_artifact(
        round_number,
        "decision.json",
        envelope.model_dump_json(indent=2),
    )
    writer.write_text(decision_json_path, envelope.model_dump_json(indent=2))

    feedback_payload = _build_feedback_payload(envelope)
    _validate_feedback_payload_for_route(feedback_payload, routing_decision)
    round_feedback_path = manager.save_artifact(
        round_number,
        "feedback.json",
        json.dumps(feedback_payload, indent=2, ensure_ascii=False),
    )

    result = {
        **dict(state),
        "current_node": "review_match",
        "status": "running",
        "pending_gate": None,
        "review_decision": routing_decision,
        "last_decision": envelope.model_dump(),
        "active_feedback": feedback_payload["feedback"],
        "artifact_refs": {
            **dict(state.get("artifact_refs") or {}),
            "last_decision_ref": str(decision_json_path.relative_to(job_root)),
            "active_feedback_ref": str(round_feedback_path.relative_to(job_root)),
            "last_proposed_state_ref": proposed_ref,
        },
    }
    _write_execution_metadata("review_match", result)
    return result


def _require_review_inputs(
    state: Mapping[str, Any],
) -> tuple[str, str, Mapping[str, Any]]:
    source = state.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("state.source is required")

    job_id = state.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("state.job_id is required")

    matched_data = state.get("matched_data")
    if not isinstance(matched_data, Mapping):
        raise ValueError("state.matched_data is required")

    matches = matched_data.get("matches")
    if not isinstance(matches, list):
        raise ValueError("state.matched_data.matches is required")

    return source, job_id, matched_data


def _compute_source_hash(matched_data: Mapping[str, Any], proposed_path: Path) -> str:
    if proposed_path.exists():
        payload = proposed_path.read_bytes()
    else:
        payload = json.dumps(
            dict(matched_data), sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def _render_decision_md(
    job_id: str,
    matched_data: Mapping[str, Any],
    source_hash: str,
    *,
    round_number: int,
) -> str:
    requirement_lookup = _build_requirement_lookup(matched_data)
    evidence_lookup = _build_evidence_lookup(matched_data)

    lines = [
        "---",
        f'source_state_hash: "{source_hash}"',
        'node: "match"',
        f'job_id: "{job_id}"',
        f"round: {round_number}",
        "---",
        "",
        "# Match Review",
        "",
        "| Req ID | Requirement | Evidence (from profile) | Score | Reasoning | Action | Comments |",
        "|---|---|---|---:|---|---|---|",
    ]

    for item in matched_data.get("matches", []):
        req_id_raw = str(item.get("req_id", ""))
        req_id = _md_cell(req_id_raw)
        requirement_text = requirement_lookup.get(
            req_id_raw, "(requirement text unavailable)"
        )
        evidence_id = str(item.get("evidence_id") or "-")
        evidence_text = _render_evidence_text(evidence_id, evidence_lookup)
        score = _safe_score(item.get("match_score", 0))
        reasoning = _md_cell(str(item.get("reasoning", "")).replace("\n", " ").strip())
        requirement_text = _md_cell(requirement_text)
        evidence_text = _md_cell(evidence_text)
        lines.append(
            f"| {req_id} | {requirement_text} | {evidence_text} | {score:.2f} | {reasoning} | [ ] Proceed / [ ] Regen / [ ] Reject | - |"
        )

    return "\n".join(lines)


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").strip()


def _safe_score(raw: Any) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


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


def _parse_decision_markdown(
    decision_text: str,
    matched_data: Mapping[str, Any],
) -> tuple[
    list[ParsedDecision] | None,
    Literal["approve", "request_regeneration", "reject"] | None,
]:
    lines = decision_text.splitlines()

    parsed_table = _parse_table_decisions(lines, matched_data)
    if parsed_table is not None and parsed_table:
        route = _route_from_parsed_decisions(parsed_table)
        return parsed_table, route
    if parsed_table is not None:
        return None, None

    parsed_blocks = _parse_per_requirement_decisions(lines)
    if parsed_blocks:
        route = _route_from_parsed_decisions(parsed_blocks)
        return parsed_blocks, route

    parsed_global = _parse_global_decision(lines)
    if parsed_global is None:
        return None, None

    route = _route_from_parsed_decisions([parsed_global])
    return [parsed_global], route


def _parse_table_decisions(
    lines: list[str],
    matched_data: Mapping[str, Any],
) -> list[ParsedDecision] | None:
    header_idx = None
    for idx, line in enumerate(lines):
        stripped = line.strip().lower()
        if (
            stripped.startswith("|")
            and "requirement" in stripped
            and "action" in stripped
            and "comments" in stripped
        ):
            header_idx = idx
            break

    if header_idx is None:
        return None

    header_cells = _split_table_row(lines[header_idx])
    if not header_cells:
        return None

    action_idx = _find_header_index(header_cells, "action")
    comments_idx = _find_header_index(header_cells, "comments")
    req_id_idx = _find_header_index(header_cells, "req id")
    if action_idx is None or comments_idx is None:
        return None

    req_ids = [
        str(item.get("req_id", "")).strip()
        for item in matched_data.get("matches", [])
        if isinstance(item, Mapping)
    ]
    req_ids = [req for req in req_ids if req]

    decisions: list[ParsedDecision] = []
    row_index = 0
    for line_number, line in enumerate(lines[header_idx + 1 :], start=header_idx + 2):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if decisions:
                break
            continue

        cells = _split_table_row(line)
        if not cells:
            continue
        if all(re.fullmatch(r"[:\-\s]+", cell or "") for cell in cells):
            continue
        if len(cells) <= max(action_idx, comments_idx):
            continue

        action_cell = cells[action_idx]
        decision, status = _parse_checkbox_decision(action_cell)
        if status == "invalid":
            raise ValueError(
                f"Line {line_number}: invalid Action markup; mark exactly one of Proceed/Regen/Reject"
            )
        if status == "none":
            return []
        if decision is None:
            return []
        decision_value = cast(
            Literal["approve", "request_regeneration", "reject"], decision
        )

        if req_id_idx is not None and req_id_idx < len(cells):
            block_id = cells[req_id_idx].strip()
            if not block_id:
                raise ValueError(f"Line {line_number}: Req ID cell cannot be empty")
        else:
            block_id = (
                req_ids[row_index]
                if row_index < len(req_ids)
                else f"row_{row_index + 1}"
            )
        comments_raw = cells[comments_idx].strip()
        comments = "" if comments_raw in {"", "-"} else comments_raw
        decisions.append(
            ParsedDecision(block_id=block_id, decision=decision_value, notes=comments)
        )
        row_index += 1

    if not decisions:
        return []
    if req_id_idx is None and req_ids and len(decisions) < len(req_ids):
        return []
    if req_id_idx is not None and req_ids:
        valid_req_ids = set(req_ids)
        unknown = sorted(
            {
                decision.block_id
                for decision in decisions
                if decision.block_id not in valid_req_ids
            }
        )
        if unknown:
            raise ValueError(
                "Decision table contains unknown Req ID values: " + ", ".join(unknown)
            )
    return decisions


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []
    return [cell.strip() for cell in stripped.split("|")[1:-1]]


def _find_header_index(header_cells: list[str], key: str) -> int | None:
    key_norm = key.strip().lower()
    for idx, cell in enumerate(header_cells):
        if cell.strip().lower() == key_norm:
            return idx
    return None


def _parse_per_requirement_decisions(lines: list[str]) -> list[ParsedDecision]:
    decisions: list[ParsedDecision] = []
    pattern = re.compile(
        r"^Decision\s*\[(?P<block>[^\]]+)\]:\s*(?P<rest>.*)$", re.IGNORECASE
    )

    idx = 0
    while idx < len(lines):
        match = pattern.match(lines[idx].strip())
        if not match:
            idx += 1
            continue

        block_id = match.group("block").strip()
        decision, status = _parse_checkbox_decision(match.group("rest"))
        if status == "none":
            return []
        if status == "invalid":
            raise ValueError(
                f"Line {idx + 1}: invalid Decision [{block_id}] markup; mark exactly one checkbox"
            )
        if decision is None:
            return []

        notes = _extract_comments_for_block(lines, idx, block_id)
        decisions.append(
            ParsedDecision(block_id=block_id, decision=decision, notes=notes)
        )
        idx += 1

    return [d for d in decisions if d.block_id.lower() != "global"]


def _parse_global_decision(lines: list[str]) -> ParsedDecision | None:
    legacy_pattern = re.compile(r"^Decision:\s*(?P<rest>.*)$", re.IGNORECASE)
    scoped_pattern = re.compile(
        r"^Decision\s*\[global\]:\s*(?P<rest>.*)$", re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        match = scoped_pattern.match(stripped) or legacy_pattern.match(stripped)
        if not match:
            continue
        decision, status = _parse_checkbox_decision(match.group("rest"))
        if status == "none":
            return None
        if status == "invalid":
            raise ValueError(
                "Invalid global decision markup; mark exactly one of Proceed/Regen/Reject"
            )
        if decision is None:
            return None
        return ParsedDecision(block_id="global", decision=decision, notes="")
    return None


def _parse_checkbox_decision(
    text: str,
) -> tuple[
    Literal["approve", "request_regeneration", "reject"] | None,
    Literal["valid", "none", "invalid"],
]:
    return parse_checkbox_decision(text)


def _extract_comments_for_block(
    lines: list[str], decision_idx: int, block_id: str
) -> str:
    marker = f"Comments [{block_id}]"
    marker_idx = None
    for idx in range(decision_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.lower().startswith("decision ["):
            break
        if stripped.lower().startswith(marker.lower()):
            marker_idx = idx
            break

    if marker_idx is None:
        return ""

    inline = lines[marker_idx].split(":", 1)
    collected: list[str] = []
    if len(inline) == 2 and inline[1].strip():
        collected.append(inline[1].strip())

    for idx in range(marker_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.lower().startswith("decision [") or stripped.lower().startswith(
            "### decision block"
        ):
            break
        if not stripped:
            if collected:
                break
            continue
        collected.append(stripped)

    return " ".join(collected).strip()


def _build_feedback_payload(envelope: DecisionEnvelope) -> dict[str, Any]:
    feedback_items: list[dict[str, Any]] = []
    for decision in envelope.decisions:
        action = _feedback_action_from_decision(decision.decision)
        reviewer_note = _strip_patch_marker(decision.notes)
        item: dict[str, Any] = {
            "req_id": decision.block_id,
            "action": action,
            "reviewer_note": reviewer_note,
        }
        patch_evidence = _extract_patch_evidence(decision.notes)
        if patch_evidence is not None:
            item["patch_evidence"] = patch_evidence
        feedback_items.append(item)

    return {
        "round_n": envelope.round,
        "feedback": feedback_items,
    }


def _feedback_action_from_decision(decision: str) -> str:
    return feedback_action_from_decision(
        cast(Literal["approve", "request_regeneration", "reject"], decision)
    )


def _validate_feedback_payload_for_route(
    payload: Mapping[str, Any],
    routing_decision: Literal["approve", "request_regeneration", "reject"],
) -> None:
    validate_feedback_payload_for_route(payload, routing_decision)


def _extract_patch_evidence(notes: str) -> dict[str, str] | None:
    marker = "PATCH_EVIDENCE:"
    upper = notes.upper()
    idx = upper.find(marker)
    if idx < 0:
        return None

    raw = notes[idx + len(marker) :].strip()
    if not raw:
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, Mapping):
        return None
    patch_id = str(payload.get("id", "")).strip()
    description = str(payload.get("description", "")).strip()
    if not patch_id or not description:
        return None
    return {"id": patch_id, "description": description}


def _strip_patch_marker(notes: str) -> str:
    marker = "PATCH_EVIDENCE:"
    upper = notes.upper()
    idx = upper.find(marker)
    if idx < 0:
        return notes.strip()
    return notes[:idx].strip()


def _route_from_parsed_decisions(
    decisions: list[ParsedDecision],
) -> Literal["approve", "request_regeneration", "reject"] | None:
    values = [
        cast(Literal["approve", "request_regeneration", "reject"], decision.decision)
        for decision in decisions
    ]
    return route_from_decision_values(values)


def _extract_round_number_from_text(text: str) -> int | None:
    for line in text.splitlines():
        match = re.match(
            r"^(?:Round|round):\s*(\d+)\s*$",
            line.strip(),
            flags=re.IGNORECASE,
        )
        if match:
            return int(match.group(1))
    return None


def _extract_source_hash_from_text(text: str) -> str | None:
    match = re.search(
        r'^\s*source_state_hash:\s*"?(sha256:[0-9a-fA-F]{64})"?\s*$',
        text,
        flags=re.MULTILINE,
    )
    if match is None:
        return None
    return match.group(1)


def _has_any_checked_decision(text: str) -> bool:
    return (
        re.search(r"\[\s*x\s*\]\s*proceed\b", text, flags=re.IGNORECASE) is not None
        or re.search(r"\[\s*x\s*\]\s*regen\b", text, flags=re.IGNORECASE) is not None
        or re.search(r"\[\s*x\s*\]\s*reject\b", text, flags=re.IGNORECASE) is not None
    )


def _effective_profile_evidence(
    state: Mapping[str, Any],
    manager: RoundManager,
) -> list[dict[str, Any]]:
    profile_evidence = state.get("my_profile_evidence")
    base = (
        [dict(item) for item in profile_evidence if isinstance(item, Mapping)]
        if isinstance(profile_evidence, list)
        else []
    )
    patches = manager.get_all_feedback_patches()
    if not patches:
        return base

    seen_ids = {
        str(item.get("id", "")).strip()
        for item in base
        if str(item.get("id", "")).strip()
    }
    for patch in patches:
        patch_id = str(patch.get("id", "")).strip()
        description = str(patch.get("description", "")).strip()
        if not patch_id or not description or patch_id in seen_ids:
            continue
        base.append({"id": patch_id, "description": description})
        seen_ids.add(patch_id)
    return base


def _write_execution_metadata(node_name: str, state: Mapping[str, Any]) -> None:
    workspace = WorkspaceManager()
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)
    service.write_node_execution_snapshot(node_name=node_name, state=state)
