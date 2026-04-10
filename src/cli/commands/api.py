"""API management command."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from src.core.api_client import LangGraphAPIClient

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("api", help="Manage the LangGraph API control plane")
    p.add_argument("action", choices=["start", "status"], help="API action")
    p.add_argument("--port", type=int, default=8124, help="Preferred API port")


async def run(args: argparse.Namespace) -> int:
    if args.action == "start":
        url = LangGraphAPIClient.ensure_server(port=args.port)
        print(url)
        return 0

    try:
        client = LangGraphAPIClient()
        if client.is_healthy():
            print(client.url)
            return 0
    except Exception as exc:
        logger.debug("LangGraph API health check raised: %s", exc)
    print("LangGraph API not reachable", file=sys.stderr)
    return 1
