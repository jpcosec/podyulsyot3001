"""CLI entry point for the document generation pipeline.

Generates tailored CV, motivation letter, and email body for a job application
based on approved matches written by the match skill.

Reads approved match artifacts from ``output/match_skill/<source>/<job_id>/``
and writes rendered documents to ``output/<source>/<job_id>/nodes/generate_documents/``.

Usage::

    python -m src.generate_documents.main \\
        --source stepstone --job-id 12345

    # With optional context overrides
    python -m src.generate_documents.main \\
        --source stepstone --job-id 12345 \\
        --profile data/profile/base_profile.json \\
        --city Berlin --receiver-name "Prof. Müller"

CLI arguments are defined in ``_build_parser()``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from src.ai.generate_documents.graph import build_default_generate_documents_chain, _make_generate_documents_node
from src.ai.generate_documents.storage import DocumentArtifactStore


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate tailored application documents from approved match artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--source", required=True, help="Job portal source name (e.g. stepstone).")
    parser.add_argument("--job-id", required=True, dest="job_id", help="Unique job posting identifier.")
    parser.add_argument(
        "--profile",
        help="Path to profile base data JSON. Defaults to data/reference_data/profile/base_profile/profile_base_data.json",
    )

    ctx = parser.add_argument_group("document context overrides")
    ctx.add_argument("--city", default=None, help="City for the letter header.")
    ctx.add_argument("--receiver-name", dest="receiver_name", default=None, help="Recipient name.")
    ctx.add_argument("--receiver-department", dest="receiver_department", default=None, help="Recipient department.")
    ctx.add_argument("--receiver-institution", dest="receiver_institution", default=None, help="Recipient institution.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run document generation for an approved match. Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    state: dict[str, Any] = {
        "source": args.source,
        "job_id": args.job_id,
    }

    if args.profile:
        try:
            state["profile_base_data"] = json.loads(
                Path(args.profile).read_text(encoding="utf-8")
            )
        except FileNotFoundError:
            parser.error(f"profile file not found: {args.profile}")
        except json.JSONDecodeError as exc:
            parser.error(f"invalid JSON in {args.profile}: {exc}")

    for key in ("city", "receiver_name", "receiver_department", "receiver_institution"):
        if value := getattr(args, key):
            state[key] = value

    try:
        chain = build_default_generate_documents_chain()
        node = _make_generate_documents_node(chain)
        result = node(state)

        output = {
            "status": result.get("status"),
            "artifact_refs": result.get("artifact_refs", {}),
        }
        print(json.dumps(output, indent=2))
        return 0

    except Exception as exc:
        print(f"[Fatal] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
