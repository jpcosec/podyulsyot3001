"""Minimal CLI runner for prep->match review flow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, cast

from src.core.ai import LLMConfig, evaluate_prep_match_run, verification_artifact_path
from src.core.io import ArtifactWriter, ObservabilityService, WorkspaceManager
from src.core.graph.state import GraphState
from src.graph import run_prep_match


def main() -> int:
    parser = argparse.ArgumentParser(description="Run prep-match graph flow")
    parser.add_argument("--source", default="tu_berlin")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--run-id", default="run-cli")
    parser.add_argument(
        "--source-url", help="Job posting URL (required for non-resume runs)"
    )
    parser.add_argument("--profile-evidence", help="Path to profile evidence JSON list")
    parser.add_argument(
        "--checkpoint-db",
        help="Path to sqlite checkpoint database (defaults to data/jobs/<source>/<job_id>/graph/checkpoint.sqlite)",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--langsmith-verifiable",
        action="store_true",
        help="Require LangSmith credentials and emit quality verification report",
    )
    args = parser.parse_args()

    cfg = LLMConfig.from_env()
    if args.langsmith_verifiable or cfg.langsmith_verification_required:
        cfg.assert_verifiable()

    if args.resume:
        state = {
            "source": args.source,
            "job_id": args.job_id,
            "run_id": args.run_id,
            "current_node": "review_match",
            "status": "pending_review",
        }
    else:
        if not args.source_url:
            raise ValueError("--source-url is required when not resuming")
        profile_evidence = _load_profile_evidence(args.profile_evidence)
        state = {
            "source": args.source,
            "job_id": args.job_id,
            "run_id": args.run_id,
            "current_node": "scrape",
            "status": "running",
            "source_url": args.source_url,
            "my_profile_evidence": profile_evidence,
            "active_feedback": [],
        }

    checkpoint_path = (
        Path(args.checkpoint_db)
        if args.checkpoint_db
        else _default_checkpoint_path(args.source, args.job_id)
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    sqlite_module = __import__("langgraph.checkpoint.sqlite", fromlist=["SqliteSaver"])
    sqlite_saver_cls = getattr(sqlite_module, "SqliteSaver")

    try:
        with sqlite_saver_cls.from_conn_string(str(checkpoint_path)) as checkpointer:
            out = run_prep_match(
                cast(GraphState, state),
                resume=args.resume,
                checkpointer=checkpointer,
                verifiable=args.langsmith_verifiable,
            )
    except Exception as exc:
        _write_run_summary_artifact(_failed_summary_state(state, exc))
        raise

    if args.langsmith_verifiable:
        verification = evaluate_prep_match_run(state, out)
        _write_verification_artifact(
            source=args.source,
            job_id=args.job_id,
            verification_report=verification,
        )

    _write_run_summary_artifact(out)

    if args.langsmith_verifiable:
        if not verification["passed"]:
            raise RuntimeError(
                "LangSmith verification failed. See graph/langsmith_verification.json"
            )

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def _load_profile_evidence(path: str | None) -> list[dict[str, Any]]:
    if path is None:
        raise ValueError("--profile-evidence is required for non-resume runs")

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, Mapping):
        evidence = _profile_base_to_evidence(payload)
        if evidence:
            return evidence

    raise ValueError(
        "profile evidence file must contain a JSON list or profile_base_data-style object"
    )


def _profile_base_to_evidence(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(description: str, prefix: str) -> None:
        text = " ".join(description.split())
        if not text:
            return
        out.append({"id": f"{prefix}_{len(out) + 1:03d}", "description": text})

    # Intentionally do not convert profile summary/tagline text into evidence.
    # Narrative fields are regenerated during CV/motivation generation phases.
    # Matching evidence must come from concrete, auditable records.

    for edu in (
        payload.get("education", [])
        if isinstance(payload.get("education"), list)
        else []
    ):
        if not isinstance(edu, Mapping):
            continue
        degree = str(edu.get("degree", "")).strip()
        institution = str(edu.get("institution", "")).strip()
        spec = str(edu.get("specialization", "")).strip()
        text = f"Education: {degree} {spec} at {institution}".strip()
        add(text, "P_EDU")

    for exp in (
        payload.get("experience", [])
        if isinstance(payload.get("experience"), list)
        else []
    ):
        if not isinstance(exp, Mapping):
            continue
        role = str(exp.get("role", "")).strip()
        org = str(exp.get("organization", "")).strip()
        achievements = exp.get("achievements")
        if isinstance(achievements, list) and achievements:
            for ach in achievements:
                if isinstance(ach, str):
                    add(f"Experience ({role} at {org}): {ach}", "P_EXP")
        else:
            add(f"Experience: {role} at {org}", "P_EXP")

    for project in (
        payload.get("projects", []) if isinstance(payload.get("projects"), list) else []
    ):
        if not isinstance(project, Mapping):
            continue
        name = str(project.get("name", "")).strip()
        stack = project.get("stack")
        stack_text = (
            ", ".join(s for s in stack if isinstance(s, str))
            if isinstance(stack, list)
            else ""
        )
        add(f"Project: {name}. Stack: {stack_text}", "P_PRJ")

    for publication in (
        payload.get("publications", [])
        if isinstance(payload.get("publications"), list)
        else []
    ):
        if not isinstance(publication, Mapping):
            continue
        title = str(publication.get("title", "")).strip()
        venue = str(publication.get("venue", "")).strip()
        add(f"Publication: {title} ({venue})", "P_PUB")

    skills = payload.get("skills")
    if isinstance(skills, Mapping):
        for key, values in skills.items():
            if not isinstance(values, list):
                continue
            terms = [v for v in values if isinstance(v, str)]
            if terms:
                add(f"Skills ({key}): {', '.join(terms)}", "P_SKL")

    languages = payload.get("languages")
    if isinstance(languages, list):
        lang_terms = []
        for item in languages:
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("name", "")).strip()
            level = str(item.get("level", "")).strip()
            if name:
                lang_terms.append(f"{name} ({level})" if level else name)
        if lang_terms:
            add(f"Languages: {', '.join(lang_terms)}", "P_LNG")

    return out


def _default_checkpoint_path(source: str, job_id: str) -> Path:
    return Path("data/jobs") / source / job_id / "graph" / "checkpoint.sqlite"


def _write_run_summary_artifact(output_state: Any) -> None:
    if not isinstance(output_state, Mapping):
        return
    workspace = WorkspaceManager()
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)
    service.write_run_summary(output_state)


def _failed_summary_state(
    base_state: Mapping[str, Any],
    error: Exception,
) -> dict[str, Any]:
    return {
        **dict(base_state),
        "status": "failed",
        "error_state": {
            "failure_type": "INTERNAL_ERROR",
            "message": str(error),
            "attempt_count": 1,
        },
    }


def _write_verification_artifact(
    *,
    source: str,
    job_id: str,
    verification_report: Mapping[str, Any],
) -> None:
    out_path = verification_artifact_path(source, job_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(dict(verification_report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
