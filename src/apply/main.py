"""CLI entry point and provider registry for job auto-application.

Usage:
    # Apply to a job
    python -m src.apply.main --source xing --job-id 12345 --cv cv.pdf [--letter letter.pdf] [--dry-run]

    # First-time session setup (mutually exclusive with apply mode)
    python -m src.apply.main --source xing --setup-session

Spec reference: docs/superpowers/specs/2026-03-30-apply-module-design.md Section 2
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import os
import sys
from pathlib import Path

from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def build_providers(data_manager: DataManager | None = None) -> dict[str, object]:
    """Lazy import adapters to avoid import-time crawl4ai initialization."""
    from src.apply.providers.stepstone.adapter import StepStoneApplyAdapter
    from src.apply.providers.xing.adapter import XingApplyAdapter

    manager = data_manager or DataManager()
    return {
        "xing": XingApplyAdapter(manager),
        "stepstone": StepStoneApplyAdapter(manager),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Job auto-application CLI")
    parser.add_argument(
        "--source",
        required=True,
        choices=["xing", "stepstone"],
        help="Job portal to apply on.",
    )
    # Apply mode
    parser.add_argument("--job-id", dest="job_id", help="Job ID to apply to.")
    parser.add_argument("--cv", dest="cv_path", help="Path to CV PDF.")
    parser.add_argument("--letter", dest="letter_path", help="Path to cover letter PDF (optional).")
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Fill form but do not submit (marcha blanca mode).",
    )
    # Session setup mode — mutually exclusive with apply mode
    parser.add_argument(
        "--setup-session",
        dest="setup_session",
        action="store_true",
        default=False,
        help="Open visible browser to log in manually. Mutually exclusive with --job-id.",
    )
    return parser


async def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv or sys.argv[1:])

    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/apply_{args.source}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    if args.setup_session and args.job_id:
        logger.error(
            "%s --setup-session and --job-id are mutually exclusive.", LogTag.FAIL
        )
        sys.exit(1)

    if args.setup_session:
        providers = build_providers()
        await providers[args.source].setup_session()
        return

    if not args.job_id or not args.cv_path:
        logger.error(
            "%s --job-id and --cv are required in apply mode.", LogTag.FAIL
        )
        sys.exit(1)

    providers = build_providers()
    meta = await providers[args.source].run(
        job_id=args.job_id,
        cv_path=Path(args.cv_path),
        letter_path=Path(args.letter_path) if args.letter_path else None,
        dry_run=args.dry_run,
    )
    logger.info("%s Apply completed: status=%s", LogTag.OK, meta.status)


if __name__ == "__main__":
    asyncio.run(main())
