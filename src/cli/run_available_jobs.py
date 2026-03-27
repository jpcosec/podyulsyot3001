"""Run prep-match continuation for available jobs from artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
import re

from src.cli.run_pipeline import _load_profile_evidence
from src.nodes.match.logic import run_logic as run_match_logic
from src.nodes.review_match.logic import run_logic as run_review_match_logic


@dataclass(frozen=True)
class JobRunResult:
    source: str
    job_id: str
    status: str
    action: str
    message: str
    review_decision: str | None = None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Continue prep-match for available jobs using on-disk artifacts"
    )
    parser.add_argument("--source", default="tu_berlin")
    parser.add_argument(
        "--job-id",
        action="append",
        help="Repeatable job id. If omitted, all numeric jobs under source are used.",
    )
    parser.add_argument("--profile-evidence", help="Profile evidence JSON path")
    parser.add_argument("--run-id", default="run-batch-recovery")
    parser.add_argument("--data-root", default="data/jobs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source_root = Path(args.data_root) / args.source
    if not source_root.exists():
        raise ValueError(f"source root not found: {source_root}")

    job_ids = _resolve_job_ids(source_root, args.job_id or [])
    needs_profile = _jobs_need_match_or_regen(source_root, job_ids)
    profile_evidence = _maybe_load_profile(args.profile_evidence, needs_profile)

    results = [
        continue_job_from_artifacts(
            source=args.source,
            job_id=job_id,
            run_id=args.run_id,
            data_root=Path(args.data_root),
            profile_evidence=profile_evidence,
            dry_run=args.dry_run,
        )
        for job_id in job_ids
    ]

    print(json.dumps([asdict(item) for item in results], indent=2, ensure_ascii=False))
    return 1 if any(item.status == "error" for item in results) else 0


def continue_job_from_artifacts(
    *,
    source: str,
    job_id: str,
    run_id: str,
    data_root: Path,
    profile_evidence: list[dict[str, Any]] | None,
    dry_run: bool,
    run_match_node: Callable[[Mapping[str, Any]], dict[str, Any]] = run_match_logic,
    run_review_node: Callable[
        [Mapping[str, Any]], dict[str, Any]
    ] = run_review_match_logic,
) -> JobRunResult:
    job_root = data_root / source / job_id
    extract_path = job_root / "nodes/extract_understand/approved/state.json"
    match_path = job_root / "nodes/match/approved/state.json"

    if not extract_path.exists():
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="error",
            action="skip",
            message="missing extract_understand approved/state.json",
        )

    extracted_data = _load_json_object(extract_path)
    if extracted_data is None:
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="error",
            action="skip",
            message="invalid extract_understand approved/state.json",
        )

    if not match_path.exists():
        return _run_match_review_cycle(
            source=source,
            job_id=job_id,
            run_id=run_id,
            extracted_data=extracted_data,
            profile_evidence=profile_evidence,
            review_decision=None,
            dry_run=dry_run,
            action="run_match_first_time",
            run_match_node=run_match_node,
            run_review_node=run_review_node,
        )

    matched_data = _load_json_object(match_path)
    if matched_data is None:
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="error",
            action="skip",
            message="invalid match approved/state.json",
        )

    review_state = {
        "source": source,
        "job_id": job_id,
        "run_id": run_id,
        "current_node": "review_match",
        "status": "pending_review",
        "matched_data": matched_data,
    }
    if dry_run:
        decision = _decision_from_active_review(job_root)
        if decision == "request_regeneration":
            return JobRunResult(
                source=source,
                job_id=job_id,
                status="planned",
                action="run_regeneration",
                message="will run match regeneration and open a new review round",
                review_decision=decision,
            )
        if decision == "approve":
            return JobRunResult(
                source=source,
                job_id=job_id,
                status="planned",
                action="complete",
                message="already approved; no regeneration needed",
                review_decision=decision,
            )
        if decision == "reject":
            return JobRunResult(
                source=source,
                job_id=job_id,
                status="planned",
                action="stop",
                message="already rejected; no regeneration needed",
                review_decision=decision,
            )
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="planned",
            action="await_review",
            message="waiting for reviewer decision in decision.md",
            review_decision=None,
        )

    try:
        reviewed = run_review_node(review_state)
    except Exception as exc:
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="error",
            action="review_parse",
            message=f"review parsing failed: {exc}",
        )

    decision = reviewed.get("review_decision")
    if decision == "approve":
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="completed",
            action="complete",
            message="approved route reached prep terminal (package)",
            review_decision="approve",
        )
    if decision == "reject":
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="completed",
            action="stop",
            message="rejected route reached terminal end",
            review_decision="reject",
        )
    if decision == "request_regeneration":
        return _run_match_review_cycle(
            source=source,
            job_id=job_id,
            run_id=run_id,
            extracted_data=extracted_data,
            profile_evidence=profile_evidence,
            review_decision="request_regeneration",
            dry_run=False,
            action="run_regeneration",
            run_match_node=run_match_node,
            run_review_node=run_review_node,
        )

    return JobRunResult(
        source=source,
        job_id=job_id,
        status="pending_review",
        action="await_review",
        message="no decision selected; review gate remains pending",
        review_decision=None,
    )


def _run_match_review_cycle(
    *,
    source: str,
    job_id: str,
    run_id: str,
    extracted_data: Mapping[str, Any],
    profile_evidence: list[dict[str, Any]] | None,
    review_decision: str | None,
    dry_run: bool,
    action: str,
    run_match_node: Callable[[Mapping[str, Any]], dict[str, Any]],
    run_review_node: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> JobRunResult:
    if profile_evidence is None:
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="error",
            action=action,
            message="--profile-evidence is required for match/regeneration",
            review_decision=review_decision,
        )
    if dry_run:
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="planned",
            action=action,
            message="planned match execution",
            review_decision=review_decision,
        )

    match_state: dict[str, Any] = {
        "source": source,
        "job_id": job_id,
        "run_id": run_id,
        "current_node": "match",
        "status": "running",
        "extracted_data": dict(extracted_data),
        "my_profile_evidence": list(profile_evidence),
    }
    if review_decision is not None:
        match_state["review_decision"] = review_decision

    try:
        matched = run_match_node(match_state)
        reviewed = run_review_node(matched)
    except Exception as exc:
        return JobRunResult(
            source=source,
            job_id=job_id,
            status="error",
            action=action,
            message=f"match/review cycle failed: {exc}",
            review_decision=review_decision,
        )

    return JobRunResult(
        source=source,
        job_id=job_id,
        status=str(reviewed.get("status", "pending_review")),
        action="await_review",
        message="match produced updated review markdown; waiting for reviewer decision",
        review_decision=reviewed.get("review_decision"),
    )


def _resolve_job_ids(source_root: Path, requested_job_ids: list[str]) -> list[str]:
    normalized = [item.strip() for item in requested_job_ids if item and item.strip()]
    if normalized:
        return normalized
    return sorted(
        path.name
        for path in source_root.iterdir()
        if path.is_dir() and path.name.isdigit()
    )


def _jobs_need_match_or_regen(source_root: Path, job_ids: list[str]) -> bool:
    for job_id in job_ids:
        job_root = source_root / job_id
        match_path = job_root / "nodes/match/approved/state.json"
        if not match_path.exists():
            return True
        if _decision_from_active_review(job_root) == "request_regeneration":
            return True
    return False


def _maybe_load_profile(
    profile_path: str | None,
    required: bool,
) -> list[dict[str, Any]] | None:
    if profile_path is None:
        if required:
            return None
        return None
    return _load_profile_evidence(profile_path)


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _decision_from_existing_json(job_root: Path) -> str | None:
    decision_json = job_root / "nodes/match/review/decision.json"
    if not decision_json.exists():
        return None

    envelope = _load_json_object(decision_json)
    if envelope is None:
        return None
    items = envelope.get("decisions")
    if not isinstance(items, list) or not items:
        return None

    values = [
        str(item.get("decision", "")).strip()
        for item in items
        if isinstance(item, Mapping)
    ]
    if not values:
        return None
    if any(v == "reject" for v in values):
        return "reject"
    if any(v == "request_regeneration" for v in values):
        return "request_regeneration"
    if all(v == "approve" for v in values):
        return "approve"
    return None


def _decision_from_active_review(job_root: Path) -> str | None:
    review_md = job_root / "nodes/match/review/decision.md"
    if review_md.exists():
        text = review_md.read_text(encoding="utf-8")
        return _decision_from_markdown_text(text)
    return _decision_from_existing_json(job_root)


def _decision_from_markdown_text(text: str) -> str | None:
    has_reject = re.search(r"\[\s*x\s*\]\s*reject\b", text, flags=re.IGNORECASE)
    has_regen = re.search(r"\[\s*x\s*\]\s*regen\b", text, flags=re.IGNORECASE)
    has_proceed = re.search(r"\[\s*x\s*\]\s*proceed\b", text, flags=re.IGNORECASE)

    if has_reject:
        return "reject"
    if has_regen:
        return "request_regeneration"
    if has_proceed:
        return "approve"
    return None


if __name__ == "__main__":
    raise SystemExit(main())
