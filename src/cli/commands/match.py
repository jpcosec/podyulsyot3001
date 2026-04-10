"""Match command."""

from __future__ import annotations

import argparse
import asyncio
import json

from src.cli.commands._utils import build_pipeline_input
from src.core.api_client import LangGraphAPIClient


async def run(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)
    initial_input = build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    result = await client.invoke_assistant(
        "generate_documents_v2",
        source=args.source,
        job_id=args.job_id,
        initial_input=initial_input,
    )

    print(json.dumps({"status": result.get("status")}, indent=2))
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("match", help="Run the match step via the LangGraph API")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", dest="job_id", required=True)
    p.add_argument("--requirements", required=True)
    p.add_argument("--profile-evidence", dest="profile_evidence", required=True)
