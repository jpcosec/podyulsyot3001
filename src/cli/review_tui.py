"""CLI entry point for the match skill HITL review TUI.

Usage::

    python -m src.cli.review_tui \\
        --source stepstone \\
        --job_id job_abc123 \\
        --thread-id <langgraph-thread-id>

The command loads the most recent review surface for the specified job from the
``MatchArtifactStore``, rebuilds the paused LangGraph thread using the provided
thread id, and launches the Textual review UI.

If ``--thread-id`` is omitted the TUI launches in **read-only preview mode**:
the review surface is displayed but submission is disabled (the Submit button
is greyed out and an informational message is shown).
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from src.match_skill.graph import create_studio_graph
from src.match_skill.storage import MatchArtifactStore
from src.ui.app import MatchReviewApp
from src.ui.bus import MatchBus


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review_tui",
        description="Launch the match skill HITL review terminal UI.",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source identifier (e.g. 'stepstone', 'xing').",
    )
    parser.add_argument(
        "--job_id",
        required=True,
        help="Job identifier whose review surface should be loaded.",
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        dest="thread_id",
        help=(
            "LangGraph thread id of the paused run. "
            "If omitted, the TUI opens in preview-only mode."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="output/match_skill",
        dest="output_dir",
        help="Root directory of the MatchArtifactStore (default: output/match_skill).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for ``python -m src.cli.review_tui``.

    Loads .env before building the graph so credentials from the project
    dotenv file are available.  Uses ``create_studio_graph()`` which already
    has a defensive demo-chain fallback — the TUI never needs to instantiate
    the real LLM just to display or submit a review of already-persisted
    artifacts.
    """
    # Load project .env so GOOGLE_API_KEY etc. are available if present.
    load_dotenv()

    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    store = MatchArtifactStore(root=args.output_dir)

    # create_studio_graph() uses the real model when credentials are present
    # and falls back to a demo chain otherwise — no hard failure on startup.
    compiled_app = create_studio_graph()

    config: dict = {}
    if args.thread_id:
        config = {"configurable": {"thread_id": args.thread_id}}

    bus = MatchBus(store=store, app=compiled_app, config=config)

    tui = MatchReviewApp(bus=bus, source=args.source, job_id=args.job_id)
    tui.run()


if __name__ == "__main__":
    main()
