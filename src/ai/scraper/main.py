"""CLI entry point and provider registry for the job portal scraper.

Dispatches scrape runs to the correct portal adapter based on ``--source``.
Logs each run to a timestamped file under ``logs/`` and prints structured
output to stdout. All portals produce ``JobPosting`` artifacts
under ``data/source/<source>/<job_id>/``.
"""

import logging
import asyncio
import os
import datetime

logger = logging.getLogger(__name__)

import argparse
from typing import List
from src.ai.scraper.providers.tuberlin.adapter import TUBerlinAdapter
from src.ai.scraper.providers.stepstone.adapter import StepStoneAdapter
from src.ai.scraper.providers.xing.adapter import XingAdapter

# Registry of available portal adapters
PROVIDERS = {
    "tuberlin": TUBerlinAdapter(),
    "stepstone": StepStoneAdapter(),
    "xing": XingAdapter()
}

def get_already_scraped_ids(data_dir: str) -> List[str]:
    """Scans the data directory to find IDs of already scraped jobs.
    
    Returns:
        A list of folder names (IDs) currently in the source directory.
    """
    if not os.path.exists(data_dir):
        return []
    return [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]

async def main():
    """Main CLI entry point for the deterministic job scraper.
    
    1. Instantiates the provider class.
    2. Builds the list of already scraped jobs (unless overwrite is active).
    3. Calls the provider's run loop with all search parameters.
    """
    parser = argparse.ArgumentParser(description="Deterministic Scraper CLI")
    parser.add_argument("--source", required=True, choices=list(PROVIDERS.keys()), 
                        help="The job portal source to crawl from.")
    parser.add_argument("--drop_repeated", action="store_true", default=True,
                        help="Skip jobs that have already been crawled (Default: True).")
    parser.add_argument("--overwrite", action="store_true", 
                        help="Ignore existing data and re-download everything.")
    parser.add_argument("--categories", nargs="+", help="Job categories to filter by.")
    parser.add_argument("--city", help="City or location to search in.")
    parser.add_argument("--job_query", help="Text search for specific professional roles or keywords.")
    parser.add_argument(
        "--max_days", type=int, help="Maximum days since the job was posted."
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of job postings to scrape."
    )
    args = parser.parse_args()
    
    # Configure logging with dynamic filename per run
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/scraper_{args.source}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )
    
    # 1. Instantiate class based on source
    adapter = PROVIDERS[args.source]
    
    # 1a. Validate search parameters and warn
    potential_params = {
        "categories": args.categories,
        "city": args.city,
        "job_query": args.job_query,
        "max_days": args.max_days
    }
    
    for param_name, value in potential_params.items():
        if value is not None and param_name not in adapter.supported_params:
            logger.warning(f"[WARNING] Provider '{args.source}' does not support filtering by '{param_name}'. This parameter will be ignored.")

    # 2. Get list of already scraped IDs (Empty if overwrite is active)
    if args.overwrite:
        already_scraped = []
        logger.info("[!] Overwrite mode active: Scanning all links regardless of existing folders.")
    else:
        already_scraped = get_already_scraped_ids("data/source")
    
    # 3. Call adapter.run with all CLI params
    # We pass args as a dict to be flexible with provider-specific params
    await adapter.run(already_scraped=already_scraped, **vars(args))

if __name__ == "__main__":
    asyncio.run(main())
