"""CLI entry point and provider registry for job ingestion.

Discovery runs crawl a source and write canonical raw job artifacts under
``data/jobs/<source>/<job_id>/nodes/ingest/proposed/``.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import os
import sys

from src.core.data_manager import DataManager
from src.scraper.providers.stepstone.adapter import StepStoneAdapter
from src.scraper.providers.tuberlin.adapter import TUBerlinAdapter
from src.scraper.providers.xing.adapter import XingAdapter
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def build_providers(data_manager: DataManager | None = None) -> dict[str, object]:
    manager = data_manager or DataManager()
    return {
        "tuberlin": TUBerlinAdapter(manager),
        "stepstone": StepStoneAdapter(manager),
        "xing": XingAdapter(manager),
    }


# TODO(future): PROVIDERS is built at import time, creating a DataManager on module load — see future_docs/issues/scraper_fragility.md
PROVIDERS = build_providers()


def get_ingested_job_ids(data_manager: DataManager, source: str) -> list[str]:
    source_root = data_manager.source_root(source)
    if not source_root.exists():
        return []
    return sorted(
        path.name
        for path in source_root.iterdir()
        if path.is_dir() and data_manager.has_ingested_job(source, path.name)
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Job discovery and ingestion CLI")
    parser.add_argument(
        "--source",
        required=True,
        choices=sorted(PROVIDERS.keys()),
        help="The job portal source to crawl from.",
    )
    parser.add_argument(
        "--drop-repeated",
        dest="drop_repeated",
        action="store_true",
        default=True,
        help="Skip jobs that already exist in canonical storage.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Ignore existing ingested jobs and fetch everything again.",
    )
    parser.add_argument("--categories", nargs="+", help="Job categories to filter by.")
    parser.add_argument("--city", help="City or location to search in.")
    parser.add_argument("--job-query", dest="job_query", help="Search keywords.")
    parser.add_argument("--max-days", dest="max_days", type=int, help="Max age filter.")
    parser.add_argument(
        "--limit", type=int, help="Limit number of job postings to ingest."
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Persist raw_page.html for each ingested job.",
    )
    return parser


async def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv or sys.argv[1:])

    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/scraper_{args.source}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    data_manager = DataManager()
    providers = build_providers(data_manager)
    adapter = providers[args.source]

    potential_params = {
        "categories": args.categories,
        "city": args.city,
        "job_query": args.job_query,
        "max_days": args.max_days,
    }
    for param_name, value in potential_params.items():
        if value is not None and param_name not in adapter.supported_params:
            logger.warning(
                "%s Provider '%s' does not support '%s'; ignoring it.",
                LogTag.WARN,
                args.source,
                param_name,
            )

    already_scraped = []
    if not args.overwrite:
        already_scraped = get_ingested_job_ids(data_manager, args.source)

    ingested_job_ids = await adapter.run(already_scraped=already_scraped, **vars(args))
    logger.info(
        "%s Ingested %s jobs for source '%s'",
        LogTag.OK,
        len(ingested_job_ids),
        args.source,
    )


if __name__ == "__main__":
    asyncio.run(main())
