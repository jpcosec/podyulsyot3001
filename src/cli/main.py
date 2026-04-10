"""Unified CLI for Postulator 3000."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Iterable

from src.core import DataManager
from src.core.api_client import LangGraphAPIClient, LangGraphConnectionError
from src.core.profile import Profile
from src.shared.log_tags import LogTag
from src.shared.logging_config import configure_logging

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_PATH = "data/reference_data/profile/base_profile/profile_base_data.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postulator",
        description="Postulator 3000 - unified operator CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    _add_api_parser(subparsers)
    _add_pipeline_parser(subparsers)
    _add_run_batch_parser(subparsers)
    _add_translate_parser(subparsers)
    _add_match_parser(subparsers)
    _add_generate_parser(subparsers)
    _add_render_parser(subparsers)
    _add_review_parser(subparsers)
    return parser


def _add_api_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("api", help="Manage the LangGraph API control plane")
    p.add_argument("action", choices=["start", "status"], help="API action")
    p.add_argument("--port", type=int, default=8124, help="Preferred API port")


def _add_pipeline_parser(subparsers: argparse._SubParsersAction) -> None:
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
        "--full-sync", action="store_true", help="Force full synchronization of profile from source."
    )


def _add_run_batch_parser(subparsers: argparse._SubParsersAction) -> None:
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
        "--full-sync", action="store_true", help="Force full synchronization of profile from source."
    )


def _add_translate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("translate", help="Run the translator only")
    p.add_argument("--source", required=True)
    p.add_argument("--target-lang", dest="target_lang", default="en")
    p.add_argument("--force", action="store_true")


def _add_match_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("match", help="Run the match step via the LangGraph API")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", dest="job_id", required=True)
    p.add_argument("--requirements", required=True)
    p.add_argument("--profile-evidence", dest="profile_evidence", required=True)


def _add_generate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate", help="Run document generation only")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", dest="job_id", required=True)
    p.add_argument("--profile")
    p.add_argument("--language", default="en")
    p.add_argument("--render", action="store_true")
    p.add_argument("--engine", default="tex", choices=["tex", "docx"])


def _add_render_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("render", help="Run document rendering only")
    p.add_argument("document", choices=["cv", "letter"])
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", dest="job_id")
    p.add_argument("--template")
    p.add_argument("--engine", default="tex", choices=["tex", "docx"])
    p.add_argument("--language", default="english")
    p.add_argument("--output")


def _add_review_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("review", help="Launch the HITL review TUI")
    p.add_argument("--source", help="Source for direct review mode")
    p.add_argument("--job-id", dest="job_id", help="Job ID for direct review mode")


def _load_json(path: str | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _build_pipeline_input(
    *,
    profile_evidence_path: str | None,
    requirements_path: str | None,
) -> dict[str, Any]:
    initial_input: dict[str, Any] = {}
    if profile_evidence_path:
        initial_input["profile_evidence"] = _load_json(profile_evidence_path)
    if requirements_path:
        initial_input["requirements"] = _load_json(requirements_path)
    return initial_input


def _translate_jobs(
    jobs: list[tuple[str, str]], *, force: bool = False
) -> list[tuple[str, str]]:
    """Translate all jobs in-place before pipeline invocation. Returns successfully translated jobs."""
    from src.core.tools.translator.main import translate_single_job, PROVIDERS
    from src.core import DataManager

    data_manager = DataManager()
    adapter = PROVIDERS["google"]
    ready: list[tuple[str, str]] = []

    for source, job_id in jobs:
        try:
            translate_single_job(data_manager, adapter, source, job_id, force=force)
            ready.append((source, job_id))
        except Exception as exc:
            logger.error(
                "%s Translation failed for %s/%s — skipping: %s",
                LogTag.FAIL,
                source,
                job_id,
                exc,
            )

    return ready


def _parse_job_selector(selector: str, sources: list[str]) -> tuple[str, str]:
    if ":" in selector:
        source, job_id = selector.split(":", 1)
        return source, job_id
    if len(sources) == 1:
        return sources[0], selector
    raise ValueError(
        f"Ambiguous job selector '{selector}'. Use source:job_id when multiple sources are provided."
    )


def _read_jobs_from_stdin(sources: list[str]) -> list[tuple[str, str]]:
    jobs: list[tuple[str, str]] = []
    for line in sys.stdin.read().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "\t" in stripped:
            source, job_id = stripped.split("\t", 1)
            jobs.append((source, job_id))
        else:
            jobs.append(_parse_job_selector(stripped, sources))
    return jobs


def _newest_jobs_for_sources(
    data_manager: DataManager, sources: list[str], limit: int | None
) -> list[tuple[str, str]]:
    jobs: list[tuple[str, str, float]] = []
    for source in sources:
        root = data_manager.source_root(source)
        if not root.exists():
            continue
        source_jobs: list[tuple[str, str, float]] = []
        for job_dir in root.iterdir():
            if not job_dir.is_dir() or not data_manager.has_ingested_job(
                source, job_dir.name
            ):
                continue
            source_jobs.append((source, job_dir.name, job_dir.stat().st_mtime))
        source_jobs.sort(key=lambda item: item[2], reverse=True)
        jobs.extend(source_jobs[:limit] if limit else source_jobs)
    jobs.sort(key=lambda item: item[2], reverse=True)
    return [(source, job_id) for source, job_id, _ in jobs]


async def _invoke_remote_pipeline(
    client: LangGraphAPIClient,
    *,
    source: str,
    job_id: str,
    source_url: str | None = None,
    initial_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return await client.invoke_pipeline(
        source=source,
        job_id=job_id,
        source_url=source_url,
        initial_input=initial_input,
    )


async def _run_api(args: argparse.Namespace) -> int:
    if args.action == "start":
        url = LangGraphAPIClient.ensure_server(port=args.port)
        print(url)
        return 0

    try:
        client = LangGraphAPIClient()
        if client.is_healthy():
            print(client.url)
            return 0
    except Exception as exc:
        logger.debug("LangGraph API health check raised: %s", exc)
    print("LangGraph API not reachable", file=sys.stderr)
    return 1


async def _sync_profile_if_needed(
    args: argparse.Namespace, client: LangGraphAPIClient
) -> None:
    """Trigger a full profile synchronization if the --full-sync flag is present."""
    if not getattr(args, "full_sync", False):
        return

    # Use the first source provided if multiple are given (for run-batch)
    source = (
        args.sources[0]
        if hasattr(args, "sources") and args.sources
        else getattr(args, "source", None)
    )
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


async def _run_pipeline(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)

    # Full sync if requested
    await _sync_profile_if_needed(args, client)

    ready = _translate_jobs([(args.source, args.job_id)])
    if not ready:
        logger.error(
            "%s Translation failed for %s/%s — aborting",
            LogTag.FAIL,
            args.source,
            args.job_id,
        )
        return 1
    initial_input = _build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    if args.auto_approve_review:
        initial_input["auto_approve_review"] = True

    thread_id = client.thread_id_for(args.source, args.job_id)
    assistant_id = "generate_documents_v2"

    logger.info(
        f"{LogTag.LLM} Starting/Resuming pipeline for {args.source}/{args.job_id}..."
    )

    # Try to start or resume
    result = await client.invoke_assistant(
        assistant_id,
        source=args.source,
        job_id=args.job_id,
        source_url=args.source_url,
        initial_input=initial_input,
    )

    # Loop while interrupted to auto-approve if requested
    while result.get("status") == "interrupted":
        if not args.auto_approve_review:
            logger.info("%s Pipeline paused for human review.", LogTag.WARN)
            break

        # Determine which node we are at
        state = await client.client.threads.get_state(thread_id)
        next_nodes = state.get("next", [])
        if not next_nodes:
            break

        target_node = next_nodes[0]
        logger.info("%s Auto-approving at %s...", LogTag.FAST, target_node)

        # Resume with empty payload (defaults to approved in the graph for auto_approve_review=True)
        result = await client.resume_thread(thread_id, {}, node_name=target_node)

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


async def _run_batch(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)

    # Full sync if requested
    await _sync_profile_if_needed(args, client)

    data_manager = DataManager()

    jobs: list[tuple[str, str]] = []
    if args.jobs:
        jobs.extend(
            _parse_job_selector(selector, args.sources) for selector in args.jobs
        )
    if args.stdin:
        jobs.extend(_read_jobs_from_stdin(args.sources))
    if not jobs:
        jobs = _newest_jobs_for_sources(data_manager, args.sources, args.limit)

    if not jobs:
        logger.warning("%s No jobs selected for batch run", LogTag.WARN)
        return 1

    jobs = _translate_jobs(jobs)
    if not jobs:
        logger.error("%s All jobs failed translation — nothing to run", LogTag.FAIL)
        return 1

    initial_input = _build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    if args.auto_approve_review:
        initial_input["auto_approve_review"] = True
    had_failures = False
    for source, job_id in jobs:
        result = await _invoke_remote_pipeline(
            client,
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


def _run_translate(args: argparse.Namespace) -> int:
    from src.core.tools.translator.main import main as translator_main

    argv = ["--source", args.source, "--target-lang", args.target_lang]
    if args.force:
        argv.append("--force")
    return translator_main(argv)


async def _run_match(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)
    initial_input = _build_pipeline_input(
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


def _run_generate(args: argparse.Namespace) -> int:
    from src.core.ai.generate_documents_v2 import generate_application_documents
    from src.core.tools.render.main import main as render_main

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


def _run_render(args: argparse.Namespace) -> int:
    from src.core.tools.render.main import main as render_main

    argv = [
        args.document,
        "--source",
        args.source,
        "--engine",
        args.engine,
        "--language",
        args.language,
    ]
    if args.job_id:
        argv.extend(["--job-id", args.job_id])
    if args.template:
        argv.extend(["--template", args.template])
    if args.output:
        argv.extend(["--output", args.output])
    return render_main(argv)


def _run_review(args: argparse.Namespace) -> int:
    from src.review_ui.app import MatchReviewApp
    from src.review_ui.bus import MatchBus
    from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore

    client = LangGraphAPIClient()
    if not client.is_healthy():
        logger.error(
            "%s Review UI requires the existing LangGraph API server that owns the current thread state.",
            LogTag.FAIL,
        )
        logger.error(
            "%s Start or keep the API server alive before launching review.",
            LogTag.WARN,
        )
        return 1
    store = PipelineArtifactStore()

    config: dict[str, Any] = {"configurable": {}}
    if args.source and args.job_id:
        config["configurable"]["thread_id"] = LangGraphAPIClient.thread_id_for(
            args.source,
            args.job_id,
        )

    bus = MatchBus(store=store, client=client, config=config)
    review_app = MatchReviewApp(bus=bus, source=args.source, job_id=args.job_id)
    review_app.run()
    return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the top-level operator CLI.

    Args:
        argv: Optional command-line arguments. Defaults to parsed process args.

    Returns:
        Process exit code where ``0`` means success.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    configure_logging()

    try:
        if args.command == "api":
            return asyncio.run(_run_api(args))
        if args.command == "pipeline":
            return asyncio.run(_run_pipeline(args))
        if args.command == "run-batch":
            return asyncio.run(_run_batch(args))
        if args.command == "translate":
            return _run_translate(args)
        if args.command == "match":
            return asyncio.run(_run_match(args))
        if args.command == "generate":
            return _run_generate(args)
        if args.command == "render":
            return _run_render(args)
        if args.command == "review":
            return _run_review(args)
        parser.print_help()
        return 1
    except LangGraphConnectionError as exc:
        logger.error("%s %s", LogTag.FAIL, exc)
        return 1
    except ValueError as exc:
        logger.error("%s %s", LogTag.FAIL, exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
