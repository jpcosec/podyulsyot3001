"""Unified CLI for Postulator 3000.

Provides subcommands for running the full pipeline or individual modules:
- pipeline: Run the full orchestration graph
- scrape: Run the scraper only
- translate: Run the translator only
- match: Run the match skill only
- generate: Run document generation only
- render: Run document rendering only
- review: Launch the HITL review TUI
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from src.core import DataManager

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postulator",
        description="Postulator 3000 - Job application pipeline with HITL review",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    _add_pipeline_parser(subparsers)
    _add_scrape_parser(subparsers)
    _add_translate_parser(subparsers)
    _add_match_parser(subparsers)
    _add_generate_parser(subparsers)
    _add_render_parser(subparsers)
    _add_review_parser(subparsers)

    return parser


def _add_pipeline_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "pipeline",
        help="Run the full pipeline (scrape → translate → match → generate → render)",
    )
    p.add_argument("--source", required=True, help="Job portal source (e.g. stepstone)")
    p.add_argument("--job-id", dest="job_id", help="Specific job ID to process")
    p.add_argument(
        "--source-url", dest="source_url", help="URL to scrape (for scrape step)"
    )
    p.add_argument(
        "--profile-evidence",
        dest="profile_evidence",
        help="Path to profile evidence JSON file",
    )
    p.add_argument(
        "--requirements",
        help="Path to requirements JSON file (or will be extracted from job)",
    )


def _add_scrape_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "scrape",
        help="Run the scraper only",
    )
    p.add_argument("--source", required=True, help="Job portal source")
    p.add_argument("--limit", type=int, help="Limit number of postings to scrape")
    p.add_argument("--overwrite", action="store_true", help="Re-download everything")
    p.add_argument("--job-query", dest="job_query", help="Search query")
    p.add_argument("--city", help="City/location filter")
    p.add_argument("--categories", nargs="+", help="Job categories")


def _add_translate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "translate",
        help="Run the translator only",
    )
    p.add_argument("--source", required=True, help="Job portal source")
    p.add_argument(
        "--target-lang",
        dest="target_lang",
        default="en",
        help="Target language (default: en)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Force re-translation even if files exist",
    )


def _add_match_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "match",
        help="Run the match skill only",
    )
    p.add_argument("--source", required=True, help="Job portal source")
    p.add_argument("--job-id", dest="job_id", required=True, help="Job posting ID")
    p.add_argument(
        "--requirements",
        required=True,
        help="Path to requirements JSON file",
    )
    p.add_argument(
        "--profile-evidence",
        dest="profile_evidence",
        required=True,
        help="Path to profile evidence JSON file",
    )


def _add_generate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "generate",
        help="Run document generation only",
    )
    p.add_argument("--source", required=True, help="Job portal source")
    p.add_argument("--job-id", dest="job_id", required=True, help="Job posting ID")
    p.add_argument(
        "--profile",
        help="Path to profile base data JSON",
    )


def _add_render_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "render",
        help="Run document rendering only",
    )
    p.add_argument("document", choices=["cv", "letter"], help="Document type")
    p.add_argument("--source", required=True, help="Source file or job source")
    p.add_argument("--job-id", dest="job_id", help="Job ID (for job-bound rendering)")
    p.add_argument("--template", help="Template/style name to use")
    p.add_argument(
        "--engine",
        default="tex",
        choices=["tex", "docx"],
        help="Rendering engine (default: tex)",
    )
    p.add_argument(
        "--language",
        default="english",
        help="Language (default: english)",
    )
    p.add_argument("--output", help="Output file path")


def _add_review_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "review",
        help="Launch the HITL review TUI",
    )
    p.add_argument("--source", required=True, help="Job portal source")
    p.add_argument("--job-id", dest="job_id", required=True, help="Job posting ID")


async def _run_pipeline(args: argparse.Namespace) -> int:
    """Run the full pipeline via the graph module."""
    from src.graph import build_pipeline_graph

    if not args.job_id:
        raise ValueError("pipeline requires --job-id in schema-v0")

    data_manager = DataManager()
    state: dict[str, Any] = {
        "source": args.source,
        "job_id": args.job_id,
        "status": "pending",
        "artifact_refs": {},
    }

    if args.source_url:
        state["source_url"] = args.source_url
    if args.profile_evidence:
        payload = json.loads(Path(args.profile_evidence).read_text(encoding="utf-8"))
        ref = data_manager.write_json_artifact(
            source=args.source,
            job_id=args.job_id,
            node_name="pipeline_inputs",
            stage="proposed",
            filename="profile_evidence.json",
            data=payload,
        )
        state["profile_evidence_ref"] = str(ref)
    if args.requirements:
        payload = json.loads(Path(args.requirements).read_text(encoding="utf-8"))
        ref = data_manager.write_json_artifact(
            source=args.source,
            job_id=args.job_id,
            node_name="pipeline_inputs",
            stage="proposed",
            filename="requirements.json",
            data={"requirements": payload},
        )
        state["artifact_refs"]["requirements_ref"] = str(ref)

    try:
        app = build_pipeline_graph()
        thread_id = f"{args.source}_{args.job_id}"
        config = {"configurable": {"thread_id": thread_id}}

        result = await app.ainvoke(state, config=config)
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


async def _run_scrape(args: argparse.Namespace) -> int:
    """Run the scraper module."""
    from src.ai.scraper.main import PROVIDERS

    adapter = PROVIDERS[args.source]
    already_scraped = []

    cli_args = {
        "source": args.source,
        "drop_repeated": True,
        "overwrite": args.overwrite,
        "job_query": args.job_query,
        "city": args.city,
        "categories": args.categories,
        "limit": args.limit,
    }

    await adapter.run(already_scraped=already_scraped, **cli_args)
    return 0


def _run_translate(args: argparse.Namespace) -> int:
    """Run the translator module."""
    from src.tools.translator.main import main as translator_main

    argv = [
        "--source",
        args.source,
        "--target-lang",
        args.target_lang,
    ]
    if args.force:
        argv.append("--force")

    return translator_main(argv)


def _run_match(args: argparse.Namespace) -> int:
    """Run the match skill module."""
    from src.ai.match_skill.main import main as match_main

    argv = [
        "--source",
        args.source,
        "--job-id",
        args.job_id,
        "--requirements",
        args.requirements,
        "--profile-evidence",
        args.profile_evidence,
    ]

    return match_main(argv)


def _run_generate(args: argparse.Namespace) -> int:
    """Run the document generation module."""
    from src.ai.generate_documents import main as generate_main

    argv = [
        "--source",
        args.source,
        "--job-id",
        args.job_id,
    ]
    if args.profile:
        argv.extend(["--profile", args.profile])

    return generate_main(argv)


def _run_render(args: argparse.Namespace) -> int:
    """Run the render module."""
    from src.tools.render.main import main as render_main

    argv = [
        args.document,
        "--source",
        args.source,
        "--engine",
        args.engine,
        "--language",
        args.language,
    ]
    if args.job_id:
        argv.extend(["--job-id", args.job_id])
    if args.template:
        argv.extend(["--template", args.template])
    if args.output:
        argv.extend(["--output", args.output])

    return render_main(argv)


def _run_review(args: argparse.Namespace) -> int:
    """Launch the HITL review TUI."""
    from src.ai.match_skill.graph import build_match_skill_graph
    from src.ai.match_skill.storage import MatchArtifactStore
    from langgraph.checkpoint.sqlite import SqliteSaver

    jobs_root = DataManager().jobs_root
    jobs_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = jobs_root / "checkpoints.db"
    store = MatchArtifactStore(jobs_root)

    thread_id = f"{args.source}_{args.job_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        with SqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            app = build_match_skill_graph(
                artifact_store=store, checkpointer=checkpointer
            )

            from src.review_ui.app import MatchReviewApp
            from src.review_ui.bus import MatchBus

            bus = MatchBus(store=store, app=app, config=config)

            review_app = MatchReviewApp(bus=bus, source=args.source, job_id=args.job_id)
            review_app.run()
            return 0
    except FileNotFoundError as e:
        print(f"[Error] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[Fatal] {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the unified CLI. Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "pipeline":
        return asyncio.run(_run_pipeline(args))
    elif args.command == "scrape":
        return asyncio.run(_run_scrape(args))
    elif args.command == "translate":
        return _run_translate(args)
    elif args.command == "match":
        return _run_match(args)
    elif args.command == "generate":
        return _run_generate(args)
    elif args.command == "render":
        return _run_render(args)
    elif args.command == "review":
        return _run_review(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
