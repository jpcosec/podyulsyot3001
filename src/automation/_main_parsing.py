"""CLI argument parsing helpers."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the canonical automation CLI parser."""
    parser = argparse.ArgumentParser(
        description="Ariadne 2.0 CLI - Semantic Browser Automation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    configure_apply_parser(subparsers)
    subparsers.add_parser(
        "browseros-check", help="Verify BrowserOS runtime connectivity"
    )
    configure_scrape_parser(subparsers)
    return parser


def configure_apply_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the apply command."""
    apply_parser = subparsers.add_parser("apply", help="Execute an Ariadne apply flow")
    add_apply_args(apply_parser)


def add_apply_args(parser) -> None:
    """Add arguments for apply command."""
    parser.add_argument(
        "--source", required=True, help="Portal source (e.g., linkedin, stepstone)"
    )
    parser.add_argument("--job-id", required=True, help="Job ID to apply to")
    parser.add_argument("--cv", required=True, help="Path to CV file")
    parser.add_argument(
        "--motor", default="browseros", help="Execution motor (browseros, crawl4ai)"
    )
    parser.add_argument("--profile", help="Path to profile JSON file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without final submission"
    )
    parser.add_argument(
        "--mode", default="easy_apply", help="Portal mode to use (default: easy_apply)"
    )
    parser.add_argument("--mission", help="Mission id to filter eligible edges")
    parser.add_argument("--resume", action="store_true", help="Resume a paused session")
    parser.add_argument("--thread-id", help="Thread ID to resume")


def configure_scrape_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the scrape command."""
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape jobs from a portal through the Ariadne graph"
    )
    scrape_parser.add_argument("--source", required=True)
    scrape_parser.add_argument("--limit", type=int, default=10)
    scrape_parser.add_argument("--motor", default="crawl4ai")
    scrape_parser.add_argument("--mode", default="search")
    scrape_parser.add_argument("--mission", default="discovery")
