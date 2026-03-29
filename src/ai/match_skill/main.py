"""CLI entry point for the match skill pipeline.

Supports two modes:

- **New run**: load requirements and profile evidence from JSON files, start a
  fresh LangGraph thread, and pause at the human review breakpoint.
- **Resume**: load a structured review payload from a JSON file and resume a
  previously paused thread through to completion.

State is persisted in a SQLite checkpoint database so threads survive process
restarts. The thread id is ``{source}_{job_id}``.

Usage::

    # Start a new match thread
    python -m src.ai.match_skill.main \\
        --source stepstone --job-id 12345 \\
        --requirements reqs.json --profile-evidence profile.json

    # Resume after HITL review
    python -m src.ai.match_skill.main \\
        --source stepstone --job-id 12345 \\
        --resume --review-payload review.json

CLI arguments are defined in ``_build_parser()``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.ai.match_skill.graph import build_match_skill_graph, resume_with_review
from src.ai.match_skill.storage import MatchArtifactStore

_DEFAULT_OUTPUT_DIR = "data/jobs"
_CHECKPOINT_DB_NAME = "checkpoints.db"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or resume the match skill pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--source", required=True, help="Job portal source name (e.g. stepstone).")
    parser.add_argument("--job-id", required=True, dest="job_id", help="Unique job posting identifier.")
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Root directory for artifacts and checkpoints. Default: {_DEFAULT_OUTPUT_DIR}",
    )

    new_run = parser.add_argument_group("new run")
    new_run.add_argument("--requirements", help="Path to requirements JSON file.")
    new_run.add_argument("--profile-evidence", dest="profile_evidence", help="Path to profile evidence JSON file.")

    resume = parser.add_argument_group("resume")
    resume.add_argument("--resume", action="store_true", help="Resume a paused thread.")
    resume.add_argument("--review-payload", dest="review_payload", help="Path to review payload JSON file (required with --resume).")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run or resume the match skill. Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.resume:
        if not args.review_payload:
            parser.error("--review-payload is required with --resume")
    else:
        if not args.requirements or not args.profile_evidence:
            parser.error("--requirements and --profile-evidence are required for a new run")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / _CHECKPOINT_DB_NAME
    store = MatchArtifactStore(output_dir)
    thread_id = f"{args.source}_{args.job_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            app = build_match_skill_graph(artifact_store=store, checkpointer=checkpointer)

            if args.resume:
                review_payload = _load_json(args.review_payload, parser)
                result = resume_with_review(app, config, review_payload)
            else:
                requirements = _load_json(args.requirements, parser)
                profile_evidence = _load_json(args.profile_evidence, parser)
                initial_state = {
                    "source": args.source,
                    "job_id": args.job_id,
                    "requirements": requirements,
                    "profile_evidence": profile_evidence,
                }
                result = app.invoke(initial_state, config=config)

            output = _build_output(result, store, args.source, args.job_id)
            print(json.dumps(output, indent=2))
            return 0

    except (ValueError, FileNotFoundError) as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[Fatal] {exc}", file=sys.stderr)
        return 1


def _load_json(path: str, parser: argparse.ArgumentParser) -> Any:
    """Load and parse a JSON file, exiting with a parser error on failure."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        parser.error(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON in {path}: {exc}")


def _build_output(result: dict[str, Any], store: MatchArtifactStore, source: str, job_id: str) -> dict[str, Any]:
    """Build a concise stdout summary from the graph result."""
    output: dict[str, Any] = {
        "status": result.get("status"),
        "review_decision": result.get("review_decision"),
    }
    review_surface = store.job_root(source, job_id) / "review" / "current.json"
    if review_surface.exists():
        output["review_surface_path"] = str(review_surface)
    return output


if __name__ == "__main__":
    sys.exit(main())
