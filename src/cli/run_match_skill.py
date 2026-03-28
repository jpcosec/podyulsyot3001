"""CLI for the LangGraph-native match skill.

This entrypoint is intentionally JSON-first:

- start a match thread from requirement and profile-evidence JSON files,
- pause at the human review breakpoint,
- resume with a structured review payload JSON file,
- persist checkpoints in SQLite so the same thread can be continued later.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver

from src.match_skill.graph import build_match_skill_graph, resume_with_review
from src.match_skill.storage import MatchArtifactStore


def main(argv: list[str] | None = None) -> int:
    """Run or resume the match skill using JSON artifacts.

    Args:
        argv: Optional explicit argv list for tests or embedding.

    Returns:
        Process exit code ``0`` on success.
    """

    args = _build_parser().parse_args(argv)
    _validate_args(args)
    store = MatchArtifactStore(args.output_dir)
    checkpoint_path = _checkpoint_path(args.output_dir, args.source, args.job_id)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": f"{args.source}_{args.job_id}"}}

    with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        app = build_match_skill_graph(checkpointer=checkpointer, artifact_store=store)
        if args.resume:
            review_payload = _load_json_file(args.review_payload)
            result = resume_with_review(app, config, review_payload)
        else:
            initial_state = {
                "source": args.source,
                "job_id": args.job_id,
                "requirements": _load_json_file(args.requirements),
                "profile_evidence": _load_json_file(args.profile_evidence),
            }
            result = app.invoke(initial_state, config=config)

    print(
        json.dumps(
            _build_cli_output(store, args.output_dir, args.source, args.job_id, result),
            indent=2,
        )
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the match skill entrypoint."""

    parser = argparse.ArgumentParser(description="Run or resume the match skill")
    parser.add_argument("--source", required=True, help="Source slug for the job")
    parser.add_argument("--job-id", required=True, help="Job identifier")
    parser.add_argument(
        "--output-dir",
        default="output/match_skill",
        help="Base directory for match skill artifacts",
    )
    parser.add_argument(
        "--requirements",
        help="Path to a JSON file containing requirement objects",
    )
    parser.add_argument(
        "--profile-evidence",
        help="Path to a JSON file containing profile evidence objects",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a paused thread using a review payload",
    )
    parser.add_argument(
        "--review-payload",
        help="Path to a JSON file containing the structured review payload",
    )
    return parser


def _build_cli_output(
    store: MatchArtifactStore,
    output_dir: str,
    source: str,
    job_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Assemble a concise JSON summary for CLI output."""

    review_path = store.job_root(source, job_id) / "review" / "current.json"
    checkpoint_path = _checkpoint_path(output_dir, source, job_id)
    payload = {
        "status": result.get("status"),
        "job": {"source": source, "job_id": job_id},
        "thread_id": f"{source}_{job_id}",
        "round_number": result.get("round_number"),
        "review_decision": result.get("review_decision"),
        "artifact_refs": result.get("artifact_refs", {}),
        "review_surface_path": str(review_path) if review_path.exists() else None,
        "checkpoint_path": str(checkpoint_path),
    }
    if result.get("active_feedback"):
        payload["active_feedback"] = result["active_feedback"]
    return payload


def _checkpoint_path(output_dir: str, source: str, job_id: str) -> Path:
    """Return the SQLite checkpoint path for a thread."""

    return Path(output_dir) / source / job_id / "graph" / "checkpoint.sqlite"


def _load_json_file(path: str | None) -> Any:
    """Load a required UTF-8 JSON file from disk."""

    if not path:
        raise ValueError("required JSON path is missing")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _validate_args(args: argparse.Namespace) -> None:
    """Validate CLI argument combinations for new runs versus resumes."""

    if args.resume:
        if not args.review_payload:
            raise ValueError("--review-payload is required with --resume")
        return

    if not args.requirements:
        raise ValueError("--requirements is required for a new run")
    if not args.profile_evidence:
        raise ValueError("--profile-evidence is required for a new run")


if __name__ == "__main__":
    raise SystemExit(main())
