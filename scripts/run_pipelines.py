"""Run full pipelines for all jobs, auto-accepting the match step."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

os.environ.setdefault(
    "PROFILE_EVIDENCE_PATH",
    "data/reference_data/profile/base_profile/profile_evidence.json",
)
os.environ.setdefault(
    "PROFILE_DATA_PATH",
    "data/reference_data/profile/base_profile/profile_base_data.json",
)

JOBS: dict[str, list[str]] = {
    "stepstone": ["12683570", "13547947", "13703696"],
    "xing": ["149995728", "150916731", "148268006"],
    "tuberlin": [],  # filled at runtime from disk
}


def _discover_tuberlin_jobs() -> list[str]:
    source_root = Path("data/jobs/tuberlin")
    if not source_root.exists():
        return []
    return sorted(
        d.name
        for d in source_root.iterdir()
        if d.is_dir() and (d / "nodes/ingest/proposed/state.json").exists()
    )


async def _auto_accept(app, config: dict, source: str, job_id: str) -> None:
    """Inject an approve-all review payload into the paused subgraph."""
    snap = await app.aget_state(config, subgraphs=True)
    if not snap.next:
        print(f"  [skip] not paused — already completed")
        return

    match_task = next((t for t in snap.tasks if t.name == "match_skill"), None)
    if not match_task or not match_task.state:
        print(f"  [error] could not find match_skill subgraph state")
        return

    subgraph_values = match_task.state.values
    match_result_hash = subgraph_values.get("match_result_hash", "")
    requirements = subgraph_values.get("requirements", [])
    req_ids = [r["id"] for r in requirements]

    review_payload = {
        "source_state_hash": match_result_hash,
        "items": [
            {"requirement_id": rid, "decision": "approve", "note": "auto-accepted"}
            for rid in req_ids
        ],
    }

    subgraph_config = match_task.state.config
    await app.aupdate_state(subgraph_config, {"review_payload": review_payload})
    print(
        f"  → approved {len(req_ids)} requirements (hash: {match_result_hash[:16]}...)"
    )


async def run_job(app, source: str, job_id: str) -> str:
    """Run full pipeline for one job, auto-accepting at the HITL step."""
    thread_id = f"{source}_{job_id}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "source": source,
        "job_id": job_id,
        "status": "pending",
        "artifact_refs": {},
    }

    print(f"\n[{source}/{job_id}] Starting pipeline...")
    result = await app.ainvoke(initial_state, config=config)
    status = result.get("status", "unknown")
    print(f"  after first invoke: status={status!r}")

    # Auto-accept if paused at HITL
    snap = await app.aget_state(config, subgraphs=True)
    if snap.next:
        print(f"  paused at: {snap.next} — injecting approve payload...")
        await _auto_accept(app, config, source, job_id)

        print(f"  resuming...")
        result = await app.ainvoke(None, config=config)
        status = result.get("status", "unknown")
        print(f"  after resume: status={status!r}")

    return status


async def main() -> None:
    from src.graph import build_pipeline_graph

    JOBS["tuberlin"] = _discover_tuberlin_jobs()
    total = sum(len(v) for v in JOBS.items())

    print(f"Jobs to run:")
    for source, ids in JOBS.items():
        print(f"  {source}: {ids}")

    app = build_pipeline_graph()
    results: list[tuple[str, str, str]] = []

    for source, job_ids in JOBS.items():
        for job_id in job_ids:
            try:
                status = await run_job(app, source, job_id)
                results.append((source, job_id, status))
            except Exception as exc:
                print(f"  [FAIL] {exc}")
                results.append((source, job_id, f"error: {exc}"))

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for source, job_id, status in results:
        icon = (
            "✓"
            if status not in ("failed", "rejected") and not status.startswith("error")
            else "✗"
        )
        print(f"  {icon} {source}/{job_id}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
