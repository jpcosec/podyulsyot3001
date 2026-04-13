"""CLI command dispatch helpers."""

import argparse
import asyncio


def extract_apply_args(args) -> dict:
    """Extract apply arguments from CLI args."""
    return {
        "source": args.source,
        "job_id": args.job_id,
        "cv_path": args.cv,
        "motor_name": args.motor,
        "profile_path": args.profile,
        "dry_run": args.dry_run,
        "portal_mode": args.mode,
        "mission_id": args.mission,
    }


def extract_scrape_args(args) -> dict:
    """Extract scrape arguments from CLI args."""
    return {
        "source": args.source,
        "limit": args.limit,
        "motor_name": args.motor,
        "portal_mode": args.mode,
        "mission_id": args.mission,
    }


def run_apply_command(args, run_apply_fn) -> int:
    """Run the apply command from parsed CLI args."""
    if args.resume and not args.thread_id:
        from src.automation._main_config import CliInputError

        raise CliInputError("--resume requires --thread-id")
    return asyncio.run(run_apply_fn(**extract_apply_args(args)))


def run_scrape_command(args, run_scrape_fn) -> int:
    """Run the scrape command from parsed CLI args."""
    return asyncio.run(run_scrape_fn(**extract_scrape_args(args)))


def run_browseros_check(base_url: str, get_adapter_fn, print_result_fn) -> int:
    """Check BrowserOS runtime health."""
    print(f"[⚡] Checking BrowserOS runtime ({base_url})...")
    adapter = get_adapter_fn("browseros")
    return print_result_fn(asyncio.run(adapter.is_healthy()), base_url)


def dispatch_command(
    args, base_url: str, parser: argparse.ArgumentParser, commands: dict
) -> int:
    """Dispatch the parsed CLI command."""
    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 0
    return handler()
