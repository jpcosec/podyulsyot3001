"""Generate command."""

from __future__ import annotations

import argparse
import json

from src.cli.commands._utils import DEFAULT_PROFILE_PATH
from src.core.ai.generate_documents_v2 import generate_application_documents
from src.core.tools.render.main import main as render_main


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the generate subcommand parser."""
    p = subparsers.add_parser("generate", help="Run document generation only")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", dest="job_id", required=True)
    p.add_argument("--profile")
    p.add_argument("--language", default="en")
    p.add_argument("--render", action="store_true")
    p.add_argument("--engine", default="tex", choices=["tex", "docx"])


def run(args: argparse.Namespace) -> int:
    profile_path = args.profile or DEFAULT_PROFILE_PATH
    result = generate_application_documents(
        source=args.source,
        job_id=args.job_id,
        profile_path=profile_path,
        target_language=args.language,
    )

    render_outputs: dict[str, int] = {}
    if args.render:
        for document in ("cv", "letter"):
            render_outputs[document] = render_main(
                [
                    document,
                    "--source",
                    args.source,
                    "--job-id",
                    args.job_id,
                    "--engine",
                    args.engine,
                    "--language",
                    args.language,
                ]
            )

    print(
        json.dumps(
            {
                "status": result.get("status"),
                "render_outputs": render_outputs,
            },
            indent=2,
        )
    )
    if args.render and any(code != 0 for code in render_outputs.values()):
        return 1
    return 0
