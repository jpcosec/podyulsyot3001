"""CLI entry point for the match skill workflow via the LangGraph API.

This command no longer instantiates local graphs or manages checkpoint storage
directly. All stateful interaction goes through the LangGraph API.

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

from src.ai.match_skill.storage import MatchArtifactStore
from src.core.api_client import LangGraphAPIClient, LangGraphConnectionError

_DEFAULT_OUTPUT_DIR = "data/jobs"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or resume the match skill pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", required=True, help="Job portal source name (e.g. stepstone)."
    )
    parser.add_argument(
        "--job-id", required=True, dest="job_id", help="Unique job posting identifier."
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Root directory for artifacts. Default: {_DEFAULT_OUTPUT_DIR}",
    )

    new_run = parser.add_argument_group("new run")
    new_run.add_argument("--requirements", help="Path to requirements JSON file.")
    new_run.add_argument(
        "--profile-evidence",
        dest="profile_evidence",
        help="Path to profile evidence JSON file.",
    )

    resume = parser.add_argument_group("resume")
    resume.add_argument("--resume", action="store_true", help="Resume a paused thread.")
    resume.add_argument(
        "--review-payload",
        dest="review_payload",
        help="Path to review payload JSON file (required with --resume).",
    )

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
            parser.error(
                "--requirements and --profile-evidence are required for a new run"
            )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    store = MatchArtifactStore(output_dir)

    try:
        url = LangGraphAPIClient.ensure_server()
        client = LangGraphAPIClient(url)

        if args.resume:
            thread_id = f"{args.source}_{args.job_id}"
            review_payload = _load_json(args.review_payload, parser)
            result = _run_async(
                client.resume_thread(thread_id, {"review_payload": review_payload})
            )
        else:
            requirements = _load_json(args.requirements, parser)
            profile_evidence = _load_json(args.profile_evidence, parser)
            result = _run_async(
                client.invoke_assistant(
                    "match_skill",
                    source=args.source,
                    job_id=args.job_id,
                    initial_input={
                        "requirements": requirements,
                        "profile_evidence": profile_evidence,
                    },
                )
            )

        output = _build_output(result, store, args.source, args.job_id)
        print(json.dumps(output, indent=2))
        return 0

    except (ValueError, FileNotFoundError) as exc:
        print(f"[Error] {exc}", file=sys.stderr)
        return 1
    except LangGraphConnectionError as exc:
        print(f"[Fatal] {exc}", file=sys.stderr)
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


def _build_output(
    result: dict[str, Any], store: MatchArtifactStore, source: str, job_id: str
) -> dict[str, Any]:
    """Build a concise stdout summary from the graph result."""
    output: dict[str, Any] = {
        "status": result.get("status"),
        "review_decision": result.get("review_decision"),
    }
    review_surface = store.job_root(source, job_id) / "review" / "current.json"
    if review_surface.exists():
        output["review_surface_path"] = str(review_surface)
    return output


def _run_async(awaitable: Any) -> Any:
    import asyncio

    return asyncio.run(awaitable)


if __name__ == "__main__":
    sys.exit(main())
