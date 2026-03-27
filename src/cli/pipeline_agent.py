"""Pipeline agent CLI for orchestrating PhD 2.0 pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.core.scraping.registry import get_scraping_registry
from src.graph import build_prep_match_node_registry, run_prep_match
from src.core.graph.state import GraphState, build_thread_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_queue_command(subparsers)
    _add_status_command(subparsers)
    _add_step_command(subparsers)
    _add_discover_command(subparsers)
    _add_sources_command(subparsers)
    _add_run_command(subparsers)

    args = parser.parse_args()

    handlers = {
        "queue": handle_queue,
        "status": handle_status,
        "step": handle_step,
        "discover": handle_discover,
        "sources": handle_sources,
        "run": handle_run,
    }

    return handlers[args.command](args)


def _add_queue_command(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("queue", help="Queue a new job in the pipeline")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", required=True)
    p.add_argument("--url", help="Job posting URL")
    p.add_argument("--profile-evidence", help="Path to profile evidence JSON list")
    p.add_argument("--run-id", default="run-cli")
    p.add_argument("--data-root", default="data/jobs")


def _add_status_command(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("status", help="Check pipeline status")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", help="Specific job ID (default: all)")
    p.add_argument("--data-root", default="data/jobs")


def _add_step_command(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("step", help="Run a specific pipeline step")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", required=True)
    p.add_argument("node", help="Node name (scrape, translate_if_needed, etc.)")
    p.add_argument("--run-id", default="run-cli")
    p.add_argument("--data-root", default="data/jobs")
    p.add_argument("--profile-evidence", help="Path to profile evidence JSON")


def _add_discover_command(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("discover", help="Discover new jobs from listing")
    p.add_argument("--source", required=True)
    p.add_argument("url", help="Listing page URL")
    p.add_argument("--max-pages", type=int, default=3)
    p.add_argument("--run-id", default="run-cli")


def _add_sources_command(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser("sources", help="List available scraping sources")


def _add_run_command(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("run", help="Run full pipeline")
    p.add_argument("--source", required=True)
    p.add_argument("--job-id", help="Job ID (if omitted, runs all pending)")
    p.add_argument("--source-url", help="Job posting URL")
    p.add_argument("--profile-evidence", help="Path to profile evidence JSON")
    p.add_argument("--run-id", default="run-cli")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--checkpoint-db", help="Path to sqlite checkpoint DB")
    p.add_argument("--data-root", default="data/jobs")


def handle_queue(args: argparse.Namespace) -> int:
    source = args.source
    job_id = args.job_id
    data_root = Path(args.data_root)
    job_root = data_root / source / job_id

    if job_root.exists():
        print(f"Job already exists: {source}/{job_id}", file=sys.stderr)
        return 1

    job_root.mkdir(parents=True, exist_ok=True)
    meta_dir = job_root / "nodes" / "_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "source": source,
        "job_id": job_id,
        "run_id": args.run_id,
        "queued_at": str(Path(__file__).stat().st_mtime),
    }
    if args.url:
        meta["source_url"] = args.url

    (meta_dir / "state.json").write_text(json.dumps(meta, indent=2))
    print(f"Queued job: {source}/{job_id}")
    return 0


def handle_status(args: argparse.Namespace) -> int:
    source = args.source
    data_root = Path(args.data_root)
    source_root = data_root / source

    if not source_root.exists():
        print(f"Source not found: {source}", file=sys.stderr)
        return 1

    job_ids = [args.job_id] if args.job_id else _list_job_ids(source_root)

    if not job_ids:
        print(f"No jobs found for source: {source}")
        return 0

    for jid in job_ids:
        status = _get_job_status(source_root / jid)
        print(f"{source}/{jid}: {status}")

    return 0


def handle_step(args: argparse.Namespace) -> int:
    source = args.source
    job_id = args.job_id
    node = args.node
    data_root = Path(args.data_root)

    valid_nodes = [
        "scrape",
        "translate_if_needed",
        "extract_understand",
        "match",
        "review_match",
        "generate_documents",
        "render",
        "package",
    ]
    if node not in valid_nodes:
        print(f"Invalid node: {node}. Valid: {valid_nodes}", file=sys.stderr)
        return 1

    job_root = data_root / source / job_id
    if not job_root.exists():
        print(f"Job not found: {source}/{job_id}", file=sys.stderr)
        return 1

    profile_evidence = None
    if args.profile_evidence:
        profile_evidence = _load_profile_evidence(args.profile_evidence)

    state: dict[str, Any] = {
        "source": source,
        "job_id": job_id,
        "run_id": args.run_id,
        "current_node": node,
        "status": "running",
    }

    if node == "scrape":
        meta = _read_job_meta(job_root)
        if not meta or "source_url" not in meta:
            print("No source_url in job meta - cannot run scrape", file=sys.stderr)
            return 1
        state["source_url"] = meta["source_url"]

    if profile_evidence:
        state["my_profile_evidence"] = profile_evidence

    previous_state = _load_previous_node_state(job_root, node)
    if previous_state:
        state = {**previous_state, **state}

    registry = build_prep_match_node_registry()
    if node not in registry:
        print(f"Node handler not found: {node}", file=sys.stderr)
        return 1

    try:
        result = registry[node](state)
    except Exception as e:
        print(f"Node execution failed: {e}", file=sys.stderr)
        return 1

    node_dir = job_root / "nodes" / node
    node_dir.mkdir(parents=True, exist_ok=True)
    (node_dir / "proposed" / "state.json").parent.mkdir(parents=True, exist_ok=True)
    (node_dir / "proposed" / "state.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )

    print(f"Executed node: {node}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def handle_discover(args: argparse.Namespace) -> int:
    from src.cli.run_scrape_probe import _run_listing

    _run_listing(
        source=args.source,
        url=args.url,
        max_pages=args.max_pages,
        run_id=args.run_id,
    )
    return 0


def handle_sources(args: argparse.Namespace) -> int:
    registry = get_scraping_registry()
    adapters = registry._adapters

    print("Available sources:")
    for key, adapter in adapters.items():
        caps = adapter.capabilities
        print(f"  - {key}: {caps.domains}")
        print(f"    listing: {caps.supports_listing}, detail: {caps.supports_detail}")

    return 0


def handle_run(args: argparse.Namespace) -> int:
    source = args.source
    job_id = args.job_id
    data_root = Path(args.data_root)

    if args.resume:
        state: dict[str, Any] = {
            "source": args.source,
            "job_id": args.job_id,
            "run_id": args.run_id,
            "current_node": "review_match",
            "status": "pending_review",
        }
    else:
        if not args.source_url:
            print("--source-url required for non-resume runs", file=sys.stderr)
            return 1
        profile_evidence = (
            _load_profile_evidence(args.profile_evidence)
            if args.profile_evidence
            else None
        )
        state = {
            "source": args.source,
            "job_id": args.job_id,
            "run_id": args.run_id,
            "current_node": "scrape",
            "status": "running",
            "source_url": args.source_url,
            "my_profile_evidence": profile_evidence or [],
            "active_feedback": [],
        }

    checkpoint_path = (
        Path(args.checkpoint_db)
        if args.checkpoint_db
        else data_root / source / job_id / "graph" / "checkpoint.sqlite"
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    sqlite_module = __import__("langgraph.checkpoint.sqlite", fromlist=["SqliteSaver"])
    sqlite_saver_cls = getattr(sqlite_module, "SqliteSaver")

    with sqlite_saver_cls.from_conn_string(str(checkpoint_path)) as checkpointer:
        out = run_prep_match(state, resume=args.resume, checkpointer=checkpointer)

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def _list_job_ids(source_root: Path) -> list[str]:
    return sorted(
        path.name
        for path in source_root.iterdir()
        if path.is_dir() and path.name.isdigit()
    )


def _get_job_status(job_root: Path) -> str:
    nodes_dir = job_root / "nodes"
    if not nodes_dir.exists():
        return "queued"

    node_order = [
        "scrape",
        "translate_if_needed",
        "extract_understand",
        "match",
        "review_match",
        "generate_documents",
        "render",
        "package",
    ]

    for i, node in enumerate(node_order):
        node_approved = nodes_dir / node / "approved"

        if node == "scrape":
            if not (node_approved / "canonical_scrape.json").exists():
                return f"pending ({node})"
        else:
            if not (node_approved / "state.json").exists():
                if node == "review_match":
                    review = nodes_dir / "match" / "review" / "decision.md"
                else:
                    review = nodes_dir / node / "review" / "decision.md"

                if review.exists():
                    decision = _parse_review_decision(review.read_text())
                    if decision == "approve":
                        continue
                    elif decision in ("request_regeneration", "reject"):
                        return f"awaiting_review ({node})"
                    else:
                        return f"awaiting_review ({node})"
                return f"pending ({node})"

    if (nodes_dir / "package" / "approved" / "state.json").exists():
        return "completed"

    last_done = None
    for node in node_order:
        node_approved = nodes_dir / node / "approved"
        if node == "scrape":
            if (node_approved / "canonical_scrape.json").exists():
                last_done = node
        else:
            if (node_approved / "state.json").exists():
                last_done = node

    if last_done:
        return f"completed ({last_done})"

    return "queued"


def _parse_review_decision(text: str) -> str | None:
    import re

    has_reject = re.search(r"\[\s*x\s*\]\s*reject\b", text, flags=re.IGNORECASE)
    has_regen = re.search(r"\[\s*x\s*\]\s*regen\b", text, flags=re.IGNORECASE)
    has_proceed = re.search(r"\[\s*x\s*\]\s*proceed\b", text, flags=re.IGNORECASE)

    if has_proceed:
        return "approve"
    if has_regen:
        return "request_regeneration"
    if has_reject:
        return "reject"
    return None


def _load_profile_evidence(path: str | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _read_job_meta(job_root: Path) -> dict[str, Any] | None:
    meta_path = job_root / "nodes" / "_meta" / "state.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_previous_node_state(job_root: Path, node: str) -> dict[str, Any] | None:
    idx = [
        "scrape",
        "translate_if_needed",
        "extract_understand",
        "match",
        "review_match",
        "generate_documents",
        "render",
        "package",
    ].index(node)

    if idx == 0:
        return None

    prev_node = idx - 1
    approved_path = (
        job_root
        / "nodes"
        / [
            "scrape",
            "translate_if_needed",
            "extract_understand",
            "match",
            "review_match",
            "generate_documents",
            "render",
            "package",
        ][prev_node]
        / "approved"
        / "state.json"
    )

    if not approved_path.exists():
        return None

    try:
        return json.loads(approved_path.read_text(encoding="utf-8"))
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
