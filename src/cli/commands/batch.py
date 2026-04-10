"""Batch pipeline command."""

from __future__ import annotations

import argparse
import asyncio
import logging

from src.cli.commands._utils import (
    DEFAULT_PROFILE_PATH,
    build_pipeline_input,
    newest_jobs_for_sources,
    parse_job_selector,
    read_jobs_from_stdin,
    translate_jobs,
)
from src.core import DataManager
from src.core.api_client import LangGraphAPIClient
from src.core.profile import Profile
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the run-batch subcommand parser."""
    p = subparsers.add_parser(
        "run-batch",
        help="Launch LangGraph pipeline runs for multiple ingested jobs",
    )
    p.add_argument("--sources", nargs="+", required=True, help="Sources to scan")
    p.add_argument(
        "--job",
        action="append",
        dest="jobs",
        help="Explicit job selector as source:job_id or just job_id when one source is used",
    )
    p.add_argument(
        "--stdin", action="store_true", help="Read source/job_id pairs from stdin"
    )
    p.add_argument(
        "--limit",
        type=int,
        help="Newest jobs per source when no explicit jobs are given",
    )
    p.add_argument("--profile-evidence", dest="profile_evidence")
    p.add_argument("--requirements")
    p.add_argument("--auto-approve-review", action="store_true")
    p.add_argument(
        "--full-sync",
        action="store_true",
        help="Force full synchronization of profile from source.",
    )


async def _sync_profile_if_needed(
    args: argparse.Namespace, client: LangGraphAPIClient
) -> None:
    if not getattr(args, "full_sync", False):
        return

    source = args.sources[0] if args.sources else None
    if not source:
        logger.warning("%s --full-sync requested but no source identified", LogTag.WARN)
        return

    profile_path = getattr(args, "profile", DEFAULT_PROFILE_PATH)
    profile = Profile(profile_path)
    try:
        await profile.refresh(client, source)
    except Exception as exc:
        logger.error("%s Profile sync failed: %s", LogTag.FAIL, exc)
        raise


async def run(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)

    await _sync_profile_if_needed(args, client)

    data_manager = DataManager()

    jobs: list[tuple[str, str]] = []
    if args.jobs:
        jobs.extend(
            parse_job_selector(selector, args.sources) for selector in args.jobs
        )
    if args.stdin:
        jobs.extend(read_jobs_from_stdin(args.sources))
    if not jobs:
        jobs = newest_jobs_for_sources(data_manager, args.sources, args.limit)

    if not jobs:
        logger.warning("%s No jobs selected for batch run", LogTag.WARN)
        return 1

    jobs = translate_jobs(jobs)
    if not jobs:
        logger.error("%s All jobs failed translation — nothing to run", LogTag.FAIL)
        return 1

    initial_input = build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    if args.auto_approve_review:
        initial_input["auto_approve_review"] = True
    had_failures = False
    for source, job_id in jobs:
        result = await client.invoke_assistant(
            "generate_documents_v2",
            source=source,
            job_id=job_id,
            initial_input=initial_input,
        )
        status = result.get("status", "unknown")
        if status == "failed":
            had_failures = True
            logger.error(
                "%s Batch run %s/%s failed: %s",
                LogTag.FAIL,
                source,
                job_id,
                result.get("error", "unknown remote error"),
            )
        else:
            logger.info(
                "%s Batch run %s/%s finished with status %s",
                LogTag.OK,
                source,
                job_id,
                status,
            )
        print(f"{source}\t{job_id}\t{status}")
    return 1 if had_failures else 0
