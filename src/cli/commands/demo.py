"""Demo command."""

from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the demo subcommand parser."""
    subparsers.add_parser("demo", help="Launch the HITL review UI demo with mock data")


def run(args: argparse.Namespace) -> int:
    from src.review_ui.demo import run_demo

    run_demo()
    return 0
