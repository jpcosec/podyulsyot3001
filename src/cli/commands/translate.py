"""Translate command."""

from __future__ import annotations

import argparse

from src.core.tools.translator.main import main as translator_main


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the translate subcommand parser."""
    p = subparsers.add_parser("translate", help="Run the translator only")
    p.add_argument("--source", required=True)
    p.add_argument("--target-lang", dest="target_lang", default="en")
    p.add_argument("--force", action="store_true")


def run(args: argparse.Namespace) -> int:
    argv = ["--source", args.source, "--target-lang", args.target_lang]
    if args.force:
        argv.append("--force")
    return translator_main(argv)
