"""Unified CLI for Postulator 3000."""

from __future__ import annotations

import argparse
import logging
import sys

from src.cli.commands import COMMAND_HANDLERS
from src.cli.commands.api import add_parser as add_api_parser
from src.cli.commands.pipeline import add_parser as add_pipeline_parser
from src.cli.commands.batch import add_parser as add_batch_parser
from src.cli.commands.translate import add_parser as add_translate_parser
from src.cli.commands.match import add_parser as add_match_parser
from src.cli.commands.generate import add_parser as add_generate_parser
from src.cli.commands.render import add_parser as add_render_parser
from src.cli.commands.review import add_parser as add_review_parser
from src.cli.commands.demo import add_parser as add_demo_parser
from src.core.api_client import LangGraphConnectionError
from src.shared.logging_config import configure_logging

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postulator",
        description="Postulator 3000 - unified operator CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_api_parser(subparsers)
    add_pipeline_parser(subparsers)
    add_batch_parser(subparsers)
    add_translate_parser(subparsers)
    add_match_parser(subparsers)
    add_generate_parser(subparsers)
    add_render_parser(subparsers)
    add_review_parser(subparsers)
    add_demo_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    configure_logging()

    try:
        handler = COMMAND_HANDLERS.get(args.command)
        if handler:
            return handler(args)
        parser.print_help()
        return 1
    except LangGraphConnectionError as exc:
        logger.error("Failed: %s", exc)
        return 1
    except ValueError as exc:
        logger.error("Invalid input: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
