"""Unified automation CLI.

Subcommands:
  scrape  — job discovery and ingestion
  apply   — job auto-application
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


def _setup_logging(label: str) -> None:
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(f"logs/{label}_{timestamp}.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


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
    p.add_argument("--backend", choices=["crawl4ai", "browseros"], default="crawl4ai")
    p.add_argument("--source", required=True, choices=["xing", "stepstone", "linkedin"])
    p.add_argument("--job-id", dest="job_id")
    p.add_argument("--cv", dest="cv_path")
    p.add_argument("--letter", dest="letter_path")
    p.add_argument("--profile-json", dest="profile_json")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    p.add_argument("--setup-session", dest="setup_session", action="store_true", default=False)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the root ArgumentParser with scrape and apply subcommands registered."""
    parser = argparse.ArgumentParser(description="Automation CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_scrape_subcommand(sub)
    _add_apply_subcommand(sub)
    return parser


async def _run_scrape(args) -> None:
    """Run a full scrape cycle using the AutomationRegistry."""
    from src.automation.registry import AutomationRegistry
    from src.automation.storage import AutomationStorage
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
    from src.automation.storage import AutomationStorage

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


async def main(argv: list[str] | None = None) -> None:
    """Parse argv and dispatch to _run_scrape or _run_apply."""
    args = build_parser().parse_args(argv or sys.argv[1:])
    if args.command == "scrape":
        await _run_scrape(args)
    elif args.command == "apply":
        await _run_apply(args)


if __name__ == "__main__":
    asyncio.run(main())
