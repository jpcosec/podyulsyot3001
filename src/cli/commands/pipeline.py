"""Pipeline command."""

from __future__ import annotations

import argparse
import asyncio
import logging

from src.cli.commands._utils import (
    DEFAULT_PROFILE_PATH,
    build_pipeline_input,
    translate_jobs,
)
from src.core.api_client import LangGraphAPIClient
from src.core.profile import Profile
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the pipeline subcommand parser."""
    p = subparsers.add_parser(
        "pipeline",
        help="Run the full pipeline via the LangGraph API",
    )
    p.add_argument("--source", required=True, help="Job portal source")
    p.add_argument("--job-id", dest="job_id", required=True, help="Job ID")
    p.add_argument("--source-url", dest="source_url", help="Source URL override")
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

    source = getattr(args, "source", None)
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

    ready = translate_jobs([(args.source, args.job_id)])
    if not ready:
        logger.error(
            "%s Translation failed for %s/%s — aborting",
            LogTag.FAIL,
            args.source,
            args.job_id,
        )
        return 1
    initial_input = build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    if args.auto_approve_review:
        initial_input["auto_approve_review"] = True

    logger.info(
        f"{LogTag.LLM} Starting/Resuming pipeline for {args.source}/{args.job_id}..."
    )

    result = await client.invoke_assistant(
        "generate_documents_v2",
        source=args.source,
        job_id=args.job_id,
        source_url=args.source_url,
        initial_input=initial_input,
    )

    while result.get("status") == "interrupted":
        if not args.auto_approve_review:
            logger.info("%s Pipeline paused for human review.", LogTag.WARN)
            break

        state = await client.client.threads.get_state(
            client.thread_id_for(args.source, args.job_id)
        )
        next_nodes = state.get("next", [])
        if not next_nodes:
            break

        target_node = next_nodes[0]
        logger.info("%s Auto-approving at %s...", LogTag.FAST, target_node)

        result = await client.resume_thread(
            client.thread_id_for(args.source, args.job_id),
            {},
            node_name=target_node,
        )

    final_status = result.get("status", "unknown")
    error_message = result.get("error")
    if final_status == "failed":
        logger.error(
            "%s Pipeline failed for %s/%s: %s",
            LogTag.FAIL,
            args.source,
            args.job_id,
            error_message or "unknown remote error",
        )
        return 1

    logger.info("%s Pipeline finished with status: %s", LogTag.OK, final_status)
    return 0
