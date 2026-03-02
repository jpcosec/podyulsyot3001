#!/usr/bin/env python3
"""Unified CLI for the PhD application data pipeline.

Thin argparse dispatcher that routes commands to step registry.
All business logic lives in src/steps/*.py.

Command structure:
  pipeline job <id> <verb> [--force] [step-specific options]
  pipeline jobs [--expiring <days>] [--expired] [--keyword <word>] [--category <cat>]
  pipeline {ingest-url|ingest-listing|archive|index|backup}
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure src is importable when run as script
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.steps import STEPS, StepResult
from src.utils.state import PIPELINE_ROOT, JobState

logger = logging.getLogger(__name__)


def main() -> int:
    """Parse CLI args and dispatch to appropriate handler."""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "job":
            return _handle_job(args)
        elif args.command == "jobs":
            return _handle_jobs(args)
        elif args.command == "ingest-url":
            return _handle_ingest_url(args)
        elif args.command == "ingest-listing":
            return _handle_ingest_listing(args)
        elif args.command == "archive":
            return _handle_archive(args)
        elif args.command == "index":
            return _handle_index(args)
        elif args.command == "backup":
            return _handle_backup(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="PhD application data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pipeline job 201084 ingest
  pipeline job 201084 match
  pipeline job 201084 render --via docx --docx-template modern
  pipeline job 201084 run
  pipeline job 201084 status
  pipeline jobs
  pipeline jobs --expiring 7
  pipeline jobs --keyword bioprocess
  pipeline ingest-url <url>
  pipeline archive 201084
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Job commands: job <id> <verb>
    job_parser = subparsers.add_parser(
        "job",
        help="Execute step or query for a specific job",
    )
    job_parser.add_argument("job_id", help="Job ID (e.g., 201084)")
    job_parser.add_argument(
        "verb",
        choices=[
            "ingest",
            "match",
            "match-approve",
            "motivate",
            "tailor-cv",
            "draft-email",
            "render",
            "package",
            "status",
            "run",
            "regenerate",
            "validate-ats",
            "template-test",
        ],
        help="Action to perform",
    )
    job_parser.add_argument(
        "--force", action="store_true", help="Re-run step even if complete"
    )
    job_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    # Step-specific options
    job_parser.add_argument(
        "--via",
        default="docx",
        choices=["docx", "latex"],
        help="Rendering engine (render step)",
    )
    job_parser.add_argument(
        "--docx-template",
        default="modern",
        choices=["classic", "modern", "harvard", "executive"],
        help="DOCX template style (render step)",
    )
    job_parser.add_argument(
        "--language",
        default="english",
        choices=["english", "german", "spanish"],
        help="Language for rendering (render step)",
    )
    job_parser.add_argument(
        "--ats-target",
        default="pdf",
        choices=["pdf", "docx"],
        help="Format to validate (validate-ats step)",
    )
    job_parser.add_argument(
        "--target",
        default="pdf",
        choices=["pdf", "docx"],
        help="Template test target (template-test step)",
    )
    job_parser.add_argument(
        "--require-perfect",
        action="store_true",
        help="Require 100%% match for template test",
    )
    job_parser.add_argument(
        "regenerate_step",
        nargs="?",
        help="Step name to regenerate (for regenerate verb)",
    )

    # Job queries: jobs [--expiring|--expired|--keyword|--category]
    jobs_parser = subparsers.add_parser(
        "jobs",
        help="List and filter open jobs",
    )
    jobs_parser.add_argument(
        "--expiring",
        type=int,
        metavar="DAYS",
        help="Show jobs with deadline within N days",
    )
    jobs_parser.add_argument(
        "--expired",
        action="store_true",
        help="Show jobs past deadline",
    )
    jobs_parser.add_argument(
        "--keyword",
        metavar="WORD",
        help="Filter by matching keyword",
    )
    jobs_parser.add_argument(
        "--category",
        metavar="CAT",
        help="Filter by job category",
    )
    jobs_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    # Ingestion helpers
    ingest_url_parser = subparsers.add_parser(
        "ingest-url",
        help="Fetch and ingest specific job URLs",
    )
    ingest_url_parser.add_argument(
        "urls", nargs="+", help="URL(s) to ingest"
    )
    ingest_url_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )
    ingest_url_parser.add_argument(
        "--strict-english",
        action="store_true",
        help="Only ingest English postings",
    )

    ingest_listing_parser = subparsers.add_parser(
        "ingest-listing",
        help="Crawl and ingest from a listing page",
    )
    ingest_listing_parser.add_argument(
        "url",
        help="Listing page URL to crawl",
    )
    ingest_listing_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )
    ingest_listing_parser.add_argument(
        "--strict-english",
        action="store_true",
        help="Only ingest English postings",
    )
    ingest_listing_parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests (seconds)",
    )

    # Archive commands
    archive_parser = subparsers.add_parser(
        "archive",
        help="Archive jobs",
    )
    archive_parser.add_argument(
        "job_id",
        nargs="?",
        help="Job ID to archive (omit to archive expired)",
    )
    archive_parser.add_argument(
        "--expired",
        action="store_true",
        help="Archive all expired jobs",
    )
    archive_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    # Admin commands
    subparsers.add_parser(
        "index",
        help="Rebuild job index",
    )
    subparsers.add_parser(
        "backup",
        help="Rebuild backup manifest",
    )

    return parser


def _handle_job(args: argparse.Namespace) -> int:
    """Handle job <id> <verb> commands."""
    job_id = args.job_id
    verb = args.verb
    source = args.source
    force = args.force

    try:
        state = JobState(job_id, source=source)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Status command (doesn't dispatch to step registry)
    if verb == "status":
        return _show_status(state)

    # Run command (execute all pending steps)
    if verb == "run":
        return _run_all_pending(state, force=force)

    # Regenerate command (re-run a specific step)
    if verb == "regenerate":
        if not args.regenerate_step:
            print(
                "Error: regenerate requires a step name",
                file=sys.stderr,
            )
            return 1
        return _regenerate_step(state, args.regenerate_step, force=True)

    # ATS validation commands (not steps in registry, special handling)
    if verb == "validate-ats":
        return _validate_ats(state, ats_target=args.ats_target, via=args.via)

    if verb == "template-test":
        return _template_test(
            state,
            via=args.via,
            docx_template=args.docx_template,
            target=args.target,
            require_perfect=args.require_perfect,
            language=args.language,
        )

    # Dispatch to step registry
    if verb not in STEPS:
        print(f"Error: unknown verb '{verb}'", file=sys.stderr)
        return 1

    return _dispatch_step(state, verb, force=force, args=args)


def _handle_jobs(args: argparse.Namespace) -> int:
    """Handle jobs [--expiring|--expired|--keyword|--category] commands."""
    source = args.source

    if args.expired:
        jobs = JobState.list_expired(source=source)
        print(f"Found {len(jobs)} expired job(s):")
    elif args.expiring:
        jobs = JobState.list_expiring(args.expiring, source=source)
        print(f"Found {len(jobs)} job(s) expiring within {args.expiring} day(s):")
    elif args.keyword:
        jobs = JobState.list_by_keyword(args.keyword, source=source)
        print(f"Found {len(jobs)} job(s) matching keyword '{args.keyword}':")
    elif args.category:
        # Filter by category (from keywords.json)
        all_jobs = JobState.list_open_jobs(source=source)
        jobs = []
        for job in all_jobs:
            try:
                kw_data = job.read_json_artifact("planning/keywords.json")
                if args.category in kw_data.get("categories", []):
                    jobs.append(job)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        print(f"Found {len(jobs)} job(s) in category '{args.category}':")
    else:
        jobs = JobState.list_open_jobs(source=source)
        print(f"Found {len(jobs)} open job(s):")

    # Format output
    for job in jobs:
        deadline_str = (
            job.deadline.isoformat() if job.deadline else "unknown"
        )
        title = job.metadata.get("title", "Unknown")
        print(f"  {job.job_id:6s}  {deadline_str}  {title}")

    return 0


def _handle_ingest_url(args: argparse.Namespace) -> int:
    """Handle ingest-url command."""
    try:
        from src.scraper.scrape_single_url import scrape_urls
    except ImportError:
        print("Error: scraper module not found", file=sys.stderr)
        return 1

    print(f"Ingesting {len(args.urls)} URL(s)...")
    try:
        scrape_urls(
            urls=args.urls,
            source=args.source,
            pipeline_root=REPO_ROOT / "data" / "pipelined_data",
            strict_english=args.strict_english,
        )
        return 0
    except Exception as e:
        logger.exception(f"Failed to ingest URLs: {e}")
        return 1


def _handle_ingest_listing(args: argparse.Namespace) -> int:
    """Handle ingest-listing command."""
    try:
        from src.scraper.fetch_listing import crawl_listing
    except ImportError:
        print("Error: scraper module not found", file=sys.stderr)
        return 1

    print(f"Crawling listing: {args.url}")
    try:
        crawl_listing(
            listing_url=args.url,
            source=args.source,
            pipeline_root=REPO_ROOT / "data" / "pipelined_data",
            strict_english=args.strict_english,
            delay=args.delay,
        )
        return 0
    except Exception as e:
        logger.exception(f"Failed to crawl listing: {e}")
        return 1


def _handle_archive(args: argparse.Namespace) -> int:
    """Handle archive command."""
    source = args.source

    if args.expired or (not args.job_id):
        # Archive all expired jobs
        expired_jobs = JobState.list_expired(source=source)
        if not expired_jobs:
            print("No expired jobs found")
            return 0
        print(f"Archiving {len(expired_jobs)} expired job(s)...")
        for job in expired_jobs:
            try:
                job.archive()
                print(f"  Archived: {job.job_id}")
            except Exception as e:
                logger.warning(f"Failed to archive {job.job_id}: {e}")
        return 0

    # Archive specific job
    if not args.job_id:
        print("Error: provide job_id or use --expired", file=sys.stderr)
        return 1

    try:
        state = JobState(args.job_id, source=source)
        state.archive()
        print(f"Archived job: {args.job_id}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _handle_index(args: argparse.Namespace) -> int:
    """Handle index command."""
    print("Rebuilding job index...")
    # This would scan PIPELINE_ROOT and rebuild any cached indices
    # For now, it's a no-op since we compute on-demand via JobState
    print("Index rebuild complete (on-demand)")
    return 0


def _handle_backup(args: argparse.Namespace) -> int:
    """Handle backup command."""
    print("Rebuilding backup manifest...")
    try:
        import subprocess
        import sys

        subprocess.run(
            [sys.executable, "src/utils/build_backup_compendium.py"],
            cwd=REPO_ROOT,
            check=True,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# ── Step dispatching ──


def _dispatch_step(
    state: JobState, verb: str, *, force: bool = False, args: argparse.Namespace | None = None
) -> int:
    """Dispatch a verb to its step function from the registry."""
    if verb not in STEPS:
        print(f"Error: unknown step verb '{verb}'", file=sys.stderr)
        return 1

    module_path, func_name = STEPS[verb]

    try:
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        print(f"Error loading step {verb}: {e}", file=sys.stderr)
        return 1

    # Build kwargs for step function
    kwargs: dict[str, Any] = {"force": force}

    # Add step-specific options from argparse
    if args:
        if verb == "render":
            kwargs.update({
                "via": args.via,
                "docx_template": args.docx_template,
                "language": args.language,
            })

    # Call step function
    try:
        result: StepResult = func(state, **kwargs)
        _print_result(result)
        return 0 if result.status == "ok" else 1
    except Exception as e:
        logger.exception(f"Step {verb} failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _run_all_pending(state: JobState, *, force: bool = False) -> int:
    """Run all pending steps in order."""
    pending = state.pending_steps()

    if not pending:
        print(f"Job {state.job_id}: all steps complete")
        return 0

    print(f"Job {state.job_id}: running {len(pending)} pending step(s)")
    print(f"  {' → '.join(pending)}")
    print()

    for step_name in pending:
        if step_name not in STEPS:
            print(f"Error: step {step_name} not in registry", file=sys.stderr)
            return 1

        verb = step_name.replace("_", "-")  # Convert internal name to verb
        print(f"[{step_name}]")

        # Create a dummy argparse namespace for dispatch
        dummy_args = argparse.Namespace(
            via="docx",
            docx_template="modern",
            language="english",
        )

        if _dispatch_step(state, verb, force=force, args=dummy_args) != 0:
            print(f"Error: step {step_name} failed", file=sys.stderr)
            return 1

        print()

    return 0


def _regenerate_step(state: JobState, step_name: str, *, force: bool = True) -> int:
    """Re-run a specific step (force=True by default)."""
    verb = step_name.replace("_", "-")  # Convert internal name to verb

    if verb not in STEPS:
        print(f"Error: step '{step_name}' not in registry", file=sys.stderr)
        return 1

    print(f"Regenerating step: {step_name}")

    # Create a dummy argparse namespace for dispatch
    dummy_args = argparse.Namespace(
        via="docx",
        docx_template="modern",
        language="english",
    )

    return _dispatch_step(state, verb, force=force, args=dummy_args)


def _show_status(state: JobState) -> int:
    """Show step completion status and comments for a job."""
    print(f"Job: {state.job_id}")
    print(f"Status: {state.status}")
    if state.deadline:
        print(f"Deadline: {state.deadline.isoformat()}")
    print()

    print("Step completion:")
    for step in state.STEP_ORDER:
        is_complete = state.step_complete(step)
        marker = "✓" if is_complete else " "
        print(f"  [{marker}] {step}")

    pending = state.pending_steps()
    if pending:
        print()
        print(f"Pending steps: {', '.join(pending)}")
        next_step = pending[0]
        print(f"Next: pipeline job {state.job_id} {next_step.replace('_', '-')}")

    return 0


def _validate_ats(state: JobState, *, ats_target: str = "pdf", via: str = "docx") -> int:
    """Validate rendered CV against job description using ATS system."""
    try:
        from src.steps.rendering import validate_ats
    except ImportError:
        print("Error: rendering module not found", file=sys.stderr)
        return 1

    try:
        report = validate_ats(state, ats_target=ats_target, via=via)
        print(f"ATS Validation Report ({ats_target}):")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _template_test(
    state: JobState,
    *,
    via: str = "docx",
    docx_template: str = "modern",
    target: str = "pdf",
    require_perfect: bool = False,
    language: str = "english",
) -> int:
    """Run deterministic parity check on rendered CV."""
    try:
        from src.steps.rendering import template_test
    except ImportError:
        print("Error: rendering module not found", file=sys.stderr)
        return 1

    try:
        report = template_test(
            state,
            via=via,
            docx_template=docx_template,
            target=target,
            require_perfect=require_perfect,
            language=language,
        )
        print(f"Template Test Report ({target}):")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _print_result(result: StepResult) -> None:
    """Pretty-print a StepResult."""
    status_marker = {
        "ok": "✓",
        "skipped": "⊘",
        "error": "✗",
    }.get(result.status, "?")

    print(f"[{status_marker}] {result.message}")
    if result.produced:
        print(f"    Produced: {', '.join(result.produced)}")
    if result.comments_found:
        print(f"    Comments found: {result.comments_found}")


if __name__ == "__main__":
    sys.exit(main())
