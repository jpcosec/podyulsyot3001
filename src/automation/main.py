"""Unified automation CLI.

Subcommands:
  scrape   — job discovery and ingestion
  apply    — job auto-application
  promote  — draft trace to canonical map
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
from pathlib import Path

from src.automation.storage import AutomationStorage


def _setup_logging(name: str) -> None:
    """Initialize structured logging for the automation module."""
    log_dir = Path("logs/automation")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    handler = logging.FileHandler(log_dir / f"{name}_{timestamp}.log")
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    
    # Also log to console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(console)


def _add_scrape_subcommand(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("scrape", help="Job discovery and ingestion")
    p.add_argument("--source", required=True, choices=["tuberlin", "stepstone", "xing"])
    p.add_argument("--drop-repeated", dest="drop_repeated", action="store_true", default=True)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--categories", nargs="+")
    p.add_argument("--city")
    p.add_argument("--job-query", dest="job_query")
    p.add_argument("--max-days", dest="max_days", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--save-html", action="store_true")


def _add_apply_subcommand(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("apply", help="Job auto-application")
    p.add_argument("--backend", choices=["crawl4ai", "browseros"], default="browseros")
    p.add_argument("--source", required=True, choices=["xing", "stepstone", "linkedin"])
    p.add_argument("--job-id", dest="job_id")
    p.add_argument("--cv", dest="cv_path")
    p.add_argument("--letter", dest="letter_path")
    p.add_argument("--profile-json", dest="profile_json")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    p.add_argument("--setup-session", dest="setup_session", action="store_true", default=False)


def _add_promote_subcommand(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("promote", help="Promote a draft trace to a canonical portal map")
    p.add_argument("--trace-id", required=True, help="ID of the session recording to promote")
    p.add_argument("--portal", required=True, help="Portal name")
    p.add_argument("--flow", default="easy_apply", help="Flow name (default: easy_apply)")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the root ArgumentParser with scrape, apply, and promote registered."""
    parser = argparse.ArgumentParser(description="Automation CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_scrape_subcommand(sub)
    _add_apply_subcommand(sub)
    _add_promote_subcommand(sub)
    return parser


async def _run_scrape(args) -> None:
    """Run a full scrape cycle using the AutomationRegistry."""
    from src.automation.registry import AutomationRegistry
    from src.shared.log_tags import LogTag

    _setup_logging(f"scrape_{args.source}")
    logger = logging.getLogger(__name__)
    storage = AutomationStorage()
    
    try:
        adapter = AutomationRegistry.get_scrape_provider(args.source, storage)
    except ValueError as e:
        logger.error("%s %s", LogTag.FAIL, e)
        sys.exit(1)

    for param, value in {"categories": args.categories, "city": args.city, "job_query": args.job_query, "max_days": args.max_days}.items():
        if value is not None and param not in adapter.supported_params:
            logger.warning("%s Provider '%s' does not support '%s'; ignoring.", LogTag.WARN, args.source, param)
    
    already_scraped: list[str] = []
    if not args.overwrite:
        source_root = storage.data_manager.source_root(args.source)
        if source_root.exists():
            already_scraped = sorted(p.name for p in source_root.iterdir() if p.is_dir() and storage.data_manager.has_ingested_job(args.source, p.name))
    
    ingested = await adapter.run(already_scraped=already_scraped, **vars(args))
    logger.info("%s Ingested %s jobs for source '%s'", LogTag.OK, len(ingested), args.source)


async def _run_apply(args) -> None:
    """Run an apply cycle using the AutomationRegistry."""
    from src.shared.log_tags import LogTag
    from src.automation.registry import AutomationRegistry

    _setup_logging(f"apply_{args.source}")
    logger = logging.getLogger(__name__)
    profile_data = None
    if args.profile_json:
        profile_data = json.loads(Path(args.profile_json).read_text(encoding="utf-8"))

    storage = AutomationStorage()
    
    try:
        adapter = AutomationRegistry.get_apply_provider(
            source=args.source, 
            backend=args.backend, 
            storage=storage, 
            profile_data=profile_data
        )
    except ValueError as e:
        logger.error("%s %s", LogTag.FAIL, e)
        sys.exit(1)

    if args.setup_session and args.job_id:
        logger.error("%s --setup-session and --job-id are mutually exclusive.", LogTag.FAIL)
        sys.exit(1)

    if args.setup_session:
        await adapter.setup_session()
        return

    if not args.job_id or not args.cv_path:
        logger.error("%s --job-id and --cv are required in apply mode.", LogTag.FAIL)
        sys.exit(1)

    meta = await adapter.run(
        job_id=args.job_id,
        cv_path=Path(args.cv_path),
        letter_path=Path(args.letter_path) if args.letter_path else None,
        dry_run=args.dry_run,
    )
    logger.info("%s Apply completed: status=%s", LogTag.OK, meta.status)


async def _run_promote(args) -> None:
    """Run the promotion workflow: normalize trace -> write to canonical map."""
    from src.automation.ariadne.normalizer import AriadneNormalizer
    from src.automation.ariadne.trace_models import AriadneSessionTrace
    from src.shared.log_tags import LogTag

    _setup_logging(f"promote_{args.portal}")
    logger = logging.getLogger(__name__)
    
    trace_path = Path(f"data/ariadne/recordings/{args.trace_id}/trace_manifest.json")
    if not trace_path.exists():
        logger.error("%s Trace manifest not found at %s", LogTag.FAIL, trace_path)
        sys.exit(1)
        
    with open(trace_path, "r") as f:
        trace = AriadneSessionTrace.model_validate(json.load(f))
        
    normalizer = AriadneNormalizer()
    portal_map = normalizer.normalize(trace)
    
    # Target path
    dest_path = Path(f"src/automation/portals/{args.portal}/maps/{args.flow}.json")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dest_path, "w") as f:
        f.write(portal_map.model_dump_json(indent=2))
        
    logger.info("%s Promoted trace '%s' to canonical map: %s", LogTag.OK, args.trace_id, dest_path)


async def main(argv: list[str] | None = None) -> None:
    """Parse argv and dispatch to subcommands."""
    args = build_parser().parse_args(argv or sys.argv[1:])
    if args.command == "scrape":
        await _run_scrape(args)
    elif args.command == "apply":
        await _run_apply(args)
    elif args.command == "promote":
        await _run_promote(args)


if __name__ == "__main__":
    asyncio.run(main())
