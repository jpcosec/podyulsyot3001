"""Review UI command."""

from __future__ import annotations

import argparse
import logging
from typing import Any

from src.core.api_client import LangGraphAPIClient
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.review_ui.app import MatchReviewApp
from src.review_ui.bus import MatchBus
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("review", help="Launch the HITL review TUI")
    p.add_argument("--source", help="Source for direct review mode")
    p.add_argument("--job-id", dest="job_id", help="Job ID for direct review mode")


def run(args: argparse.Namespace) -> int:
    client = LangGraphAPIClient()
    if not client.is_healthy():
        logger.error(
            "%s Review UI requires the existing LangGraph API server that owns the current thread state.",
            LogTag.FAIL,
        )
        logger.error(
            "%s Start or keep the API server alive before launching review.",
            LogTag.WARN,
        )
        return 1
    store = PipelineArtifactStore()

    config: dict[str, Any] = {"configurable": {}}
    if args.source and args.job_id:
        config["configurable"]["thread_id"] = LangGraphAPIClient.thread_id_for(
            args.source,
            args.job_id,
        )

    bus = MatchBus(store=store, client=client, config=config)
    review_app = MatchReviewApp(bus=bus, source=args.source, job_id=args.job_id)
    review_app.run()
    return 0
