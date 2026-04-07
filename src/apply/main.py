"""CLI entry point and provider registry for job auto-application.

Usage:
    # Apply to a job
    python -m src.apply.main --source xing --job-id 12345 --cv cv.pdf [--letter letter.pdf] [--dry-run]

    # First-time session setup (mutually exclusive with apply mode)
    python -m src.apply.main --source xing --setup-session

Design reference: `src/apply/README.md`
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import sys
from pathlib import Path

from src.apply.browseros_backend import build_browseros_providers
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag
from src.shared.logging_config import configure_logging

logger = logging.getLogger(__name__)


def build_crawl4ai_providers(
    data_manager: DataManager | None = None,
) -> dict[str, object]:
    """Lazy import adapters to avoid import-time crawl4ai initialization."""
    from src.apply.providers.linkedin.adapter import LinkedInApplyAdapter
    from src.apply.providers.stepstone.adapter import StepStoneApplyAdapter
    from src.apply.providers.xing.adapter import XingApplyAdapter

    manager = data_manager or DataManager()
    return {
        "linkedin": LinkedInApplyAdapter(manager),
        "xing": XingApplyAdapter(manager),
        "stepstone": StepStoneApplyAdapter(manager),
    }


def build_providers(
    backend: str,
    data_manager: DataManager | None = None,
    profile_data: dict | None = None,
) -> dict[str, object]:
    """Build provider instances for the requested execution backend.

    Args:
        backend: Backend name such as ``crawl4ai`` or ``browseros``.
        data_manager: Optional shared data manager for artifact IO.
        profile_data: Optional candidate profile payload for BrowserOS runs.

    Returns:
        A mapping from source name to instantiated provider.
    """
    if backend == "browseros":
        return build_browseros_providers(data_manager, profile_data=profile_data)
    return build_crawl4ai_providers(data_manager)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for apply operations.

    Returns:
        The configured argument parser for session setup and apply execution.
    """
    parser = argparse.ArgumentParser(description="Job auto-application CLI")
    parser.add_argument(
        "--backend",
        choices=["crawl4ai", "browseros"],
        default="crawl4ai",
        help="Execution backend for apply automation.",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["xing", "stepstone", "linkedin"],
        help="Job portal to apply on.",
    )
    # Apply mode
    parser.add_argument("--job-id", dest="job_id", help="Job ID to apply to.")
    parser.add_argument("--cv", dest="cv_path", help="Path to CV PDF.")
    parser.add_argument(
        "--letter", dest="letter_path", help="Path to cover letter PDF (optional)."
    )
    parser.add_argument(
        "--profile-json",
        dest="profile_json",
        help="Optional JSON file with candidate fields for BrowserOS playbooks.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Fill the form and capture artifacts without submitting it.",
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
    """Run the apply CLI.

    Args:
        argv: Optional command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        None. Exits the process for invalid CLI usage.
    """
    args = build_parser().parse_args(argv or sys.argv[1:])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    configure_logging(log_file=f"apply_{args.source}_{timestamp}.log")

    if args.setup_session and args.job_id:
        logger.error(
            "%s --setup-session and --job-id are mutually exclusive.", LogTag.FAIL
        )
        sys.exit(1)

    profile_data = None
    if args.profile_json:
        profile_data = json.loads(Path(args.profile_json).read_text(encoding="utf-8"))

    providers = build_providers(args.backend, profile_data=profile_data)
    if args.source not in providers:
        logger.error(
            "%s Backend '%s' does not support source '%s'.",
            LogTag.FAIL,
            args.backend,
            args.source,
        )
        sys.exit(1)

    if args.setup_session:
        await providers[args.source].setup_session()
        return

    if not args.job_id or not args.cv_path:
        logger.error("%s --job-id and --cv are required in apply mode.", LogTag.FAIL)
        sys.exit(1)

    meta = await providers[args.source].run(
        job_id=args.job_id,
        cv_path=Path(args.cv_path),
        letter_path=Path(args.letter_path) if args.letter_path else None,
        dry_run=args.dry_run,
    )
    logger.info("%s Apply completed: status=%s", LogTag.OK, meta.status)


if __name__ == "__main__":
    asyncio.run(main())
