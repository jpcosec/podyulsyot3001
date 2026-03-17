"""Logic for generating document deltas and deterministic review indicators."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.ai.prompt_manager import PromptManager
from src.ai.runtime import LLMRuntime
from src.nodes.generate_documents.contract import (
    DocumentDeltas,
    TextReviewAssistEnvelope,
    TextReviewIndicator,
)

DEFAULT_PROFILE_BASE_PATH = Path(
    "data/reference_data/profile/base_profile/profile_base_data.json"
)

FORBIDDEN_PHRASES = (
    "excellent",
    "expert",
    "passionate",
    "perfect",
    "ideal",
    "highly skilled",
    "incredible",
    "proven track record",
    "successful",
    "driven",
    "dynamic",
    "enthusiastic",
)


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Generate document deltas and deterministic assist indicators."""
    input_data, profile_data = _build_input_data(state)

    prompt_manager = PromptManager(base_path="src/nodes")
    model_name = os.getenv("PHD2_GEMINI_MODEL", "gemini-2.5-flash")
    runtime = LLMRuntime(model_name=model_name)

    system_prompt, user_prompt = prompt_manager.build_prompt(
        "generate_documents",
        input_data,
        required_xml_tags=("candidate_base_cv", "validated_matches"),
        optional_xml_tags=(),
    )

    result = runtime.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_schema=DocumentDeltas,
    )

    deltas_payload = result.model_dump()
    _validate_injection_ids(deltas_payload, profile_data)

    source_hash = _compute_payload_hash(deltas_payload)
    assist_envelope = _build_assist_envelope(
        node="generate_documents",
        job_id=input_data["job_id"],
        source_state_hash=source_hash,
        deltas_payload=deltas_payload,
        approved_matches=input_data["approved_matches"],
    )

    rendered_docs = _render_documents(state, profile_data, deltas_payload)
    refs = _persist_artifacts(state, deltas_payload, assist_envelope, rendered_docs)

    artifact_refs = dict(state.get("artifact_refs") or {})
    if refs.get("state_ref"):
        artifact_refs["last_proposed_state_ref"] = refs["state_ref"]

    return {
        **dict(state),
        "current_node": "generate_documents",
        "status": "running",
        "document_deltas": deltas_payload,
        "text_review_indicators": [
            indicator.model_dump() for indicator in assist_envelope.indicators
        ],
        "artifact_refs": artifact_refs,
    }


def _build_input_data(
    state: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    job_id = state.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("state.job_id is required")

    profile_base = _load_profile_base_data(state)
    profile_data = _normalize_profile_data(profile_base)

    matched_data = state.get("matched_data")
    if not isinstance(matched_data, Mapping):
        raise ValueError("state.matched_data is required")

    extracted_data = state.get("extracted_data")
    requirements = (
        extracted_data.get("requirements")
        if isinstance(extracted_data, Mapping)
        and isinstance(extracted_data.get("requirements"), list)
        else []
    )
    req_lookup = _build_requirement_lookup(requirements)

    decision_envelope = _load_match_decision_envelope(state)
    approved_matches, human_patches = _resolve_validated_matches(
        decision_envelope,
        matched_data,
        req_lookup,
    )

    return (
        {
            "job_id": job_id,
            "filtered_profile_json": json.dumps(
                profile_data, indent=2, ensure_ascii=False
            ),
            "approved_matches": approved_matches,
            "human_patches": human_patches,
        },
        profile_data,
    )


def _load_profile_base_data(state: Mapping[str, Any]) -> dict[str, Any]:
    profile_from_state = state.get("profile_base_data")
    if isinstance(profile_from_state, Mapping):
        return dict(profile_from_state)

    if not DEFAULT_PROFILE_BASE_PATH.exists():
        raise ValueError(
            "profile_base_data is missing and default profile snapshot file was not found"
        )

    payload = json.loads(DEFAULT_PROFILE_BASE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("profile_base_data snapshot must be a JSON object")
    return dict(payload)


def _normalize_profile_data(profile: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(profile)

    experiences_raw = (
        profile.get("experience") if isinstance(profile.get("experience"), list) else []
    )
    normalized_experiences: list[dict[str, Any]] = []
    for idx, item in enumerate(experiences_raw, start=1):
        if not isinstance(item, Mapping):
            continue
        copied = dict(item)
        exp_id = str(copied.get("id", "")).strip() or f"EXP{idx:03d}"
        copied["id"] = exp_id
        normalized_experiences.append(copied)

    normalized["experience"] = normalized_experiences

    publications_raw = (
        profile.get("publications")
        if isinstance(profile.get("publications"), list)
        else []
    )
    normalized_publications: list[dict[str, Any]] = []
    for item in publications_raw:
        if not isinstance(item, Mapping):
            continue
        copied = dict(item)
        copied.setdefault("url", "")
        normalized_publications.append(copied)
    normalized["publications"] = normalized_publications

    languages_raw = (
        profile.get("languages") if isinstance(profile.get("languages"), list) else []
    )
    normalized_languages: list[dict[str, Any]] = []
    for item in languages_raw:
        if not isinstance(item, Mapping):
            continue
        copied = dict(item)
        copied.setdefault("note", "")
        normalized_languages.append(copied)
    normalized["languages"] = normalized_languages

    return normalized


def _build_requirement_lookup(requirements: list[Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in requirements:
        if not isinstance(item, Mapping):
            continue
        req_id = str(item.get("id", "")).strip()
        req_text = " ".join(str(item.get("text", "")).split()).strip()
        if req_id and req_text:
            out[req_id] = req_text
    return out


def _load_match_decision_envelope(state: Mapping[str, Any]) -> Mapping[str, Any]:
    last_decision = state.get("last_decision")
    if isinstance(last_decision, Mapping) and isinstance(
        last_decision.get("decisions"), list
    ):
        return last_decision

    source = state.get("source")
    job_id = state.get("job_id")
    if (
        isinstance(source, str)
        and source.strip()
        and isinstance(job_id, str)
        and job_id.strip()
    ):
        decision_path = (
            Path("data/jobs")
            / source.strip()
            / job_id.strip()
            / "nodes/match/review/decision.json"
        )
        if decision_path.exists():
            payload = json.loads(decision_path.read_text(encoding="utf-8"))
            if isinstance(payload, Mapping) and isinstance(
                payload.get("decisions"), list
            ):
                return payload

    raise ValueError(
        "latest match decision envelope is required (state.last_decision or nodes/match/review/decision.json)"
    )


def _resolve_validated_matches(
    decision_envelope: Mapping[str, Any],
    matched_data: Mapping[str, Any],
    req_lookup: Mapping[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matches_raw = (
        matched_data.get("matches")
        if isinstance(matched_data.get("matches"), list)
        else []
    )

    match_by_req: dict[str, Mapping[str, Any]] = {}
    for item in matches_raw:
        if not isinstance(item, Mapping):
            continue
        req_id = str(item.get("req_id", "")).strip()
        if req_id:
            match_by_req[req_id] = item

    approved: list[dict[str, Any]] = []
    patches: list[dict[str, Any]] = []

    decisions = decision_envelope.get("decisions")
    if not isinstance(decisions, list):
        return approved, patches

    has_global = any(
        isinstance(item, Mapping)
        and str(item.get("block_id", "")).strip().lower() == "global"
        for item in decisions
    )
    if has_global:
        global_entries = [
            item
            for item in decisions
            if isinstance(item, Mapping)
            and str(item.get("block_id", "")).strip().lower() == "global"
        ]
        if global_entries:
            global_decision = str(global_entries[-1].get("decision", "")).strip()
            global_notes = " ".join(str(global_entries[-1].get("notes", "")).split())
            if global_decision == "approve":
                approved = _all_approved_matches(match_by_req, req_lookup)
                return approved, patches
            if global_decision == "request_regeneration":
                patches.append(
                    {
                        "req": "global",
                        "human_note": global_notes,
                        "evidence_id": None,
                    }
                )
                return approved, patches
            return approved, patches

    for decision in decisions:
        if not isinstance(decision, Mapping):
            continue
        block_id = str(decision.get("block_id", "")).strip()
        decision_value = str(decision.get("decision", "")).strip()
        notes = " ".join(str(decision.get("notes", "")).split()).strip()
        match_item = match_by_req.get(block_id)
        req_text = req_lookup.get(block_id, block_id)

        if decision_value == "approve" and match_item is not None:
            approved.append(
                {
                    "req": req_text,
                    "req_id": block_id,
                    "evidence_id": match_item.get("evidence_id"),
                    "reasoning": match_item.get("reasoning"),
                }
            )
        elif decision_value == "request_regeneration":
            patches.append(
                {
                    "req": req_text,
                    "req_id": block_id,
                    "human_note": notes,
                    "evidence_id": (match_item or {}).get("evidence_id"),
                }
            )

    return approved, patches


def _all_approved_matches(
    match_by_req: Mapping[str, Mapping[str, Any]],
    req_lookup: Mapping[str, str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for req_id, item in match_by_req.items():
        out.append(
            {
                "req": req_lookup.get(req_id, req_id),
                "req_id": req_id,
                "evidence_id": item.get("evidence_id"),
                "reasoning": item.get("reasoning"),
            }
        )
    return out


def _validate_injection_ids(
    deltas_payload: Mapping[str, Any],
    profile_data: Mapping[str, Any],
) -> None:
    experience = (
        profile_data.get("experience")
        if isinstance(profile_data.get("experience"), list)
        else []
    )
    valid_ids = {
        str(item.get("id", "")).strip()
        for item in experience
        if isinstance(item, Mapping) and str(item.get("id", "")).strip()
    }
    if not valid_ids:
        raise ValueError("profile experience ids are required for cv injections")

    injections = (
        deltas_payload.get("cv_injections")
        if isinstance(deltas_payload.get("cv_injections"), list)
        else []
    )
    for item in injections:
        if not isinstance(item, Mapping):
            raise ValueError("cv_injections entries must be objects")
        exp_id = str(item.get("experience_id", "")).strip()
        if exp_id not in valid_ids:
            raise ValueError(
                f"cv_injections references unknown experience_id: {exp_id}"
            )


def _build_assist_envelope(
    *,
    node: str,
    job_id: str,
    source_state_hash: str,
    deltas_payload: Mapping[str, Any],
    approved_matches: list[dict[str, Any]],
) -> TextReviewAssistEnvelope:
    indicators = _build_indicators(deltas_payload, approved_matches)
    summary = (
        "No deterministic warnings detected"
        if not indicators
        else f"{len(indicators)} deterministic warning(s) detected"
    )
    return TextReviewAssistEnvelope(
        node=node,
        job_id=job_id,
        source_state_hash=source_state_hash,
        indicators=indicators,
        summary=summary,
    )


def _build_indicators(
    deltas_payload: Mapping[str, Any], approved_matches: list[dict[str, Any]]
) -> list[TextReviewIndicator]:
    indicators: list[TextReviewIndicator] = []

    flattened_text = _flatten_text(deltas_payload)
    for idx, phrase in enumerate(FORBIDDEN_PHRASES, start=1):
        pattern = _phrase_to_regex(phrase)
        if re.search(pattern, flattened_text, flags=re.IGNORECASE):
            indicators.append(
                TextReviewIndicator(
                    severity="major",
                    category="tone",
                    rule_id=f"ANTI_FLUFF_{idx:03d}",
                    target_ref="global",
                    message=f"Detected forbidden style phrase: '{phrase}'",
                    evidence_refs=[],
                )
            )

    if not approved_matches:
        indicators.append(
            TextReviewIndicator(
                severity="major",
                category="grounding",
                rule_id="GROUNDING_001",
                target_ref="global",
                message="No approved requirement/evidence matches were provided to generation",
                evidence_refs=[],
            )
        )

    summary_lines = _non_empty_lines(str(deltas_payload.get("cv_summary", "")))
    if len(summary_lines) > 3:
        indicators.append(
            TextReviewIndicator(
                severity="major",
                category="format",
                rule_id="FORMAT_001",
                target_ref="cv_summary",
                message="CV summary exceeds 3 non-empty lines",
                evidence_refs=[],
            )
        )

    email_lines = _non_empty_lines(str(deltas_payload.get("email_body", "")))
    if len(email_lines) > 2:
        indicators.append(
            TextReviewIndicator(
                severity="major",
                category="format",
                rule_id="FORMAT_002",
                target_ref="email_body",
                message="Email body exceeds 2 non-empty lines",
                evidence_refs=[],
            )
        )

    return indicators


def _phrase_to_regex(phrase: str) -> str:
    escaped = [re.escape(part) for part in phrase.split()]
    return r"\b" + r"\s+".join(escaped) + r"\b"


def _flatten_text(value: Any) -> str:
    out: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            for child in node.values():
                walk(child)
            return
        if isinstance(node, list):
            for child in node:
                walk(child)
            return
        if isinstance(node, str):
            out.append(node)

    walk(value)
    return "\n".join(out)


def _non_empty_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def _render_documents(
    state: Mapping[str, Any],
    profile_data: Mapping[str, Any],
    deltas_payload: Mapping[str, Any],
) -> dict[str, str]:
    template_root = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_root)),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    receiver_name = str(
        state.get("receiver_name") or "[Receiver Name / Hiring Committee]"
    )
    receiver_department = str(
        state.get("receiver_department") or "[Department / Faculty]"
    )
    receiver_institution = str(
        state.get("receiver_institution") or "[Institution / Company]"
    )
    city = str(state.get("receiver_city") or "Berlin")

    context = {
        "profile": profile_data,
        "document_deltas": deltas_payload,
        "current_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "city": city,
        "receiver_name": receiver_name,
        "receiver_department": receiver_department,
        "receiver_institution": receiver_institution,
    }

    return {
        "cv_markdown": env.get_template("cv_template.jinja2").render(**context),
        "letter_markdown": env.get_template("cover_letter_template.jinja2").render(
            **context
        ),
        "email_markdown": env.get_template("email_template.jinja2").render(**context),
    }


def _persist_artifacts(
    state: Mapping[str, Any],
    deltas_payload: Mapping[str, Any],
    assist_envelope: TextReviewAssistEnvelope,
    rendered_docs: Mapping[str, str],
) -> dict[str, str]:
    source = state.get("source")
    job_id = state.get("job_id")
    if not isinstance(source, str) or not source.strip():
        return {}
    if not isinstance(job_id, str) or not job_id.strip():
        return {}

    job_root = Path("data/jobs") / source.strip() / job_id.strip()
    node_root = job_root / "nodes" / "generate_documents"

    approved_dir = node_root / "approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    state_path = approved_dir / "state.json"
    state_path.write_text(
        json.dumps(deltas_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    proposed_dir = node_root / "proposed"
    proposed_dir.mkdir(parents=True, exist_ok=True)
    (proposed_dir / "cv.md").write_text(rendered_docs["cv_markdown"], encoding="utf-8")
    (proposed_dir / "motivation_letter.md").write_text(
        rendered_docs["letter_markdown"], encoding="utf-8"
    )
    (proposed_dir / "application_email.md").write_text(
        rendered_docs["email_markdown"], encoding="utf-8"
    )

    assist_dir = node_root / "assist" / "proposed"
    assist_dir.mkdir(parents=True, exist_ok=True)
    assist_state_path = assist_dir / "state.json"
    assist_state_path.write_text(
        assist_envelope.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    (assist_dir / "view.md").write_text(
        _render_assist_view(assist_envelope),
        encoding="utf-8",
    )

    return {
        "state_ref": str(state_path.relative_to(job_root)),
        "assist_ref": str(assist_state_path.relative_to(job_root)),
    }


def _render_assist_view(envelope: TextReviewAssistEnvelope) -> str:
    lines = [
        "# Deterministic Text Review Indicators",
        "",
        f"- Node: {envelope.node}",
        f"- Job ID: {envelope.job_id}",
        f"- Source hash: {envelope.source_state_hash}",
        f"- Summary: {envelope.summary}",
        "",
    ]

    if not envelope.indicators:
        lines.append("No warnings detected.")
        return "\n".join(lines)

    lines.extend(
        [
            "| Severity | Category | Rule | Target | Message |",
            "|---|---|---|---|---|",
        ]
    )
    for indicator in envelope.indicators:
        lines.append(
            "| "
            f"{indicator.severity} | {indicator.category} | {indicator.rule_id} | "
            f"{indicator.target_ref} | {indicator.message} |"
        )
    return "\n".join(lines)


def _compute_payload_hash(payload: Mapping[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return f"sha256:{hashlib.sha256(data).hexdigest()}"
