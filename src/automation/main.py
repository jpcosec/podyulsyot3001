#!/usr/bin/env python3
"""CLI entrypoint for Ariadne browser automation flows."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import time
import traceback
import uuid
from typing import Optional

import requests

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.ariadne.models import AriadneMap, AriadneState
from src.automation.ariadne.repository import MapRepository
from src.automation.contracts import CandidateProfile
from src.automation.motors.registry import MotorRegistry


class CliInputError(ValueError):
    """Raised when CLI inputs are invalid before execution starts."""


class CliExecutionError(RuntimeError):
    """Raised when a CLI flow cannot be started or completed."""


def _build_parser() -> argparse.ArgumentParser:
    """Build the canonical automation CLI parser."""
    parser = argparse.ArgumentParser(
        description="Ariadne 2.0 CLI - Semantic Browser Automation"
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    apply_parser = subparsers.add_parser("apply", help="Execute an Ariadne apply flow")
    apply_parser.add_argument(
        "--source", required=True, help="Portal source (e.g., linkedin, stepstone)"
    )
    apply_parser.add_argument("--job-id", required=True, help="Job ID to apply to")
    apply_parser.add_argument("--cv", required=True, help="Path to CV file")
    apply_parser.add_argument(
        "--motor", default="browseros", help="Execution motor (browseros, crawl4ai)"
    )
    apply_parser.add_argument("--profile", help="Path to profile JSON file")
    apply_parser.add_argument(
        "--dry-run", action="store_true", help="Run without final submission"
    )
    apply_parser.add_argument(
        "--mode", default="easy_apply", help="Portal mode to use (default: easy_apply)"
    )
    apply_parser.add_argument("--mission", help="Mission id to filter eligible edges")
    apply_parser.add_argument(
        "--resume", action="store_true", help="Resume a paused session"
    )
    apply_parser.add_argument("--thread-id", help="Thread ID to resume")

    subparsers.add_parser(
        "browseros-check", help="Verify BrowserOS runtime connectivity"
    )

    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape jobs from a portal through the Ariadne graph"
    )
    scrape_parser.add_argument("--source", required=True)
    scrape_parser.add_argument("--limit", type=int, default=10)
    scrape_parser.add_argument("--motor", default="crawl4ai")
    scrape_parser.add_argument("--mode", default="search")
    scrape_parser.add_argument("--mission", default="discovery")

    return parser


def _default_profile() -> CandidateProfile:
    """Return a deterministic fallback profile for local runs."""
    return CandidateProfile(
        first_name="Ariadne",
        last_name="Pilot",
        email="ariadne@example.com",
        phone="+49 176 00000000",
        address="Semantic Way 1",
        city="Berlin",
        zip="10115",
    )


def _load_profile(profile_path: Optional[str]) -> CandidateProfile:
    """Load a user profile or return the local fallback profile."""
    if profile_path and os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as handle:
            return CandidateProfile(**json.load(handle))
    return _default_profile()


def _load_map(source: str, portal_mode: str) -> AriadneMap:
    """Load and validate the requested Ariadne map."""
    repo = MapRepository()
    try:
        return repo.get_map(source, map_type=portal_mode)
    except FileNotFoundError as exc:
        raise CliExecutionError(str(exc)) from exc
    except ValueError as exc:
        raise CliExecutionError(f"Failed to validate map: {exc}") from exc


def _get_executor(motor_name: str):
    """Resolve an executor instance from the motor registry."""
    try:
        return MotorRegistry.get_executor(motor_name)
    except ValueError as exc:
        raise CliInputError(str(exc)) from exc


def _build_config(executor, motor_name: str, thread_id: str) -> dict:
    """Build a shared graph execution config."""
    return {
        "configurable": {
            "thread_id": thread_id,
            "executor": executor,
            "motor_name": motor_name,
            "record_graph": True,
        }
    }


def _print_updates(chunk: dict) -> None:
    """Render streamed node updates for interactive CLI runs."""
    for node_name, state_update in chunk.items():
        print(f"[⚡] Node: {node_name}")
        for err in state_update.get("errors", []):
            print(f"    [⚠️] ERROR: {err}")
        if "current_state_id" in state_update:
            print(f"    [⚡] Map State: {state_update['current_state_id']}")


async def _run_graph(initial_state: AriadneState, config: dict):
    """Run one Ariadne graph session and return the final state snapshot."""
    async with create_ariadne_graph() as app:
        async for chunk in app.astream(initial_state, config, stream_mode="updates"):
            _print_updates(chunk)
        return await app.aget_state(config)


def _build_apply_state(
    source: str,
    job_id: str,
    cv_path: str,
    profile: CandidateProfile,
    ariadne_map: AriadneMap,
    dry_run: bool,
    portal_mode: str,
    mission_id: Optional[str],
) -> AriadneState:
    """Construct the initial state for an apply run."""
    entry_state = (
        "job_details"
        if "job_details" in ariadne_map.states
        else next(iter(ariadne_map.states))
    )
    return {
        "job_id": job_id,
        "portal_name": source,
        "profile_data": profile.model_dump(),
        "job_data": {
            "job_id": job_id,
            "cv_path": os.path.abspath(cv_path),
            "dry_run": dry_run,
        },
        "path_id": str(uuid.uuid4()),
        "current_mission_id": mission_id or portal_mode,
        "current_state_id": entry_state,
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": portal_mode,
        "patched_components": {},
    }


def _build_scrape_state(
    source: str,
    limit: int,
    ariadne_map: AriadneMap,
    portal_mode: str,
    mission_id: str,
) -> AriadneState:
    """Construct the initial state for a scrape run."""
    entry_state = (
        "search_results"
        if "search_results" in ariadne_map.states
        else next(iter(ariadne_map.states))
    )
    return {
        "job_id": f"discovery-{source}-{uuid.uuid4().hex[:8]}",
        "portal_name": source,
        "profile_data": {},
        "job_data": {"limit": limit},
        "path_id": str(uuid.uuid4()),
        "current_mission_id": mission_id,
        "current_state_id": entry_state,
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {"limit": limit},
        "errors": [],
        "history": [],
        "portal_mode": portal_mode,
        "patched_components": {},
    }


async def run_apply(
    source: str,
    job_id: str,
    cv_path: str,
    motor_name: str = "browseros",
    profile_path: Optional[str] = None,
    dry_run: bool = False,
    portal_mode: str = "easy_apply",
    mission_id: Optional[str] = None,
) -> int:
    """Execute an apply mission through the Ariadne graph."""
    print("\n[⚡] Ariadne 2.0: Starting Apply Flow")
    print(f"   Portal: {source}")
    print(f"   Job ID: {job_id}")
    print(f"   CV: {cv_path}")
    print(f"   Motor: {motor_name}")
    print(f"   Dry Run: {dry_run}\n")

    ariadne_map = _load_map(source, portal_mode)
    print(
        f"[✅] Loaded Map: {ariadne_map.meta.source} {ariadne_map.meta.flow} (v{ariadne_map.meta.version})"
    )

    profile = _load_profile(profile_path)
    print(f"[✅] Loaded Profile: {profile.first_name} {profile.last_name}")

    initial_state = _build_apply_state(
        source,
        job_id,
        cv_path,
        profile,
        ariadne_map,
        dry_run,
        portal_mode,
        mission_id,
    )
    executor = _get_executor(motor_name)
    thread_id = str(uuid.uuid4())
    config = _build_config(executor, motor_name, thread_id)

    print("[⚡] Compiling Ariadne Graph...")
    print("[⚡] Beginning JIT Execution...\n")

    final_state = await _run_graph(initial_state, config)
    if final_state.next and final_state.next[0] == "human_in_the_loop":
        print("\n[⚠️] Apply Paused: Human-In-The-Loop required.")
        print(
            "    Instructions: The graph has reached a safety breakpoint or an unknown state."
        )
        print(
            f"    To resume, run: python -m src.automation.main apply --resume --thread-id {thread_id}"
        )
        return 0

    state_values = final_state.values
    current_map_state = state_values.get("current_state_id")
    if current_map_state in ariadne_map.success_states:
        print("\n[✅] Apply Success: Mission Completed.")
        return 0
    if state_values.get("errors"):
        print("\n[❌] Apply Terminated with Errors.")
        for err in state_values["errors"]:
            print(f"    - {err}")
        return 1

    print(f"\n[⚠️] Apply Stopped at State: {current_map_state}")
    return 0


async def run_scrape(
    source: str,
    limit: int,
    motor_name: str = "crawl4ai",
    portal_mode: str = "search",
    mission_id: str = "discovery",
) -> int:
    """Execute a discovery mission through the Ariadne graph."""
    print("\n[⚡] Ariadne 2.0: Starting Discovery Flow")
    print(f"   Portal: {source}")
    print(f"   Limit: {limit}")
    print(f"   Motor: {motor_name}")
    print(f"   Mission: {mission_id}\n")

    ariadne_map = _load_map(source, portal_mode)
    print(
        f"[✅] Loaded Map: {ariadne_map.meta.source} {ariadne_map.meta.flow} (v{ariadne_map.meta.version})"
    )

    initial_state = _build_scrape_state(
        source, limit, ariadne_map, portal_mode, mission_id
    )
    executor = _get_executor(motor_name)
    thread_id = str(uuid.uuid4())
    config = _build_config(executor, motor_name, thread_id)

    print("[⚡] Compiling Ariadne Graph...")

    # Handle async context manager for crawl4ai motor
    if motor_name == "crawl4ai":
        async with executor as active_executor:
            config["configurable"]["executor"] = active_executor
            final_state = await _run_graph(initial_state, config)
    else:
        final_state = await _run_graph(initial_state, config)
    state_values = final_state.values
    extracted_payload = state_values.get("session_memory", {})

    if state_values.get("current_state_id") in ariadne_map.success_states:
        print("\n[✅] Discovery Success: Mission Completed.")
    elif state_values.get("errors"):
        print("\n[❌] Discovery Terminated with Errors.")
        for err in state_values["errors"]:
            print(f"    - {err}")
        return 1
    else:
        print(
            f"\n[⚠️] Discovery Stopped at State: {state_values.get('current_state_id')}"
        )

    print("\n[📦] Extracted Session Memory")
    print(json.dumps(extracted_payload, indent=2, sort_keys=True))
    return 0


def _check_browseros_running(base_url: str = "http://127.0.0.1:9000") -> bool:
    """Check if BrowserOS is running at the given base URL."""
    try:
        resp = requests.get(f"{base_url}/mcp", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def _launch_browseros(appimage_path: str) -> subprocess.Popen:
    """Launch BrowserOS via AppImage and return the process handle."""
    return subprocess.Popen(
        [appimage_path, "--no-sandbox"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _ensure_browseros(base_url: str = "http://127.0.0.1:9000") -> None:
    """Ensure BrowserOS is running. Auto-start if BROWSEROS_APPIMAGE_PATH is set."""
    if _check_browseros_running(base_url):
        return

    appimage_path = os.environ.get("BROWSEROS_APPIMAGE_PATH")
    if not appimage_path:
        raise CliExecutionError(f"BrowserOS not running at {base_url}")

    print(f"[⚡] Launching BrowserOS from {appimage_path}...")
    proc = _launch_browseros(appimage_path)

    for _ in range(30):
        time.sleep(1)
        if _check_browseros_running(base_url):
            print(f"[✅] BrowserOS running at {base_url}")
            return

    proc.kill()
    raise CliExecutionError("BrowserOS failed to start within 30s")
    if not appimage_path:
        print("[❌] BROWSEROS_APPIMAGE_PATH not set")
        raise CliExecutionError("Cannot auto-start: BROWSEROS_APPIMAGE_PATH not set")

    print(f"[⚡] Launching BrowserOS from {appimage_path}...")
    proc = _launch_browseros(appimage_path)

    for _ in range(30):
        time.sleep(1)
        if _check_browseros_running(base_url):
            print(f"[✅] BrowserOS running at {base_url}")
            return

    proc.kill()
    raise CliExecutionError("BrowserOS failed to start within 30s")


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args, dispatch commands, and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    base_url = os.environ.get("BROWSEROS_BASE_URL", "http://127.0.0.1:9000")

    try:
        if args.command in ("apply", "scrape", "crawl"):
            _ensure_browseros(base_url=base_url)

        if args.command == "apply":
            if args.resume and not args.thread_id:
                raise CliInputError("--resume requires --thread-id")
            return asyncio.run(
                run_apply(
                    source=args.source,
                    job_id=args.job_id,
                    cv_path=args.cv,
                    motor_name=args.motor,
                    profile_path=args.profile,
                    dry_run=args.dry_run,
                    portal_mode=args.mode,
                    mission_id=args.mission,
                )
            )

        if args.command == "browseros-check":
            print(f"[⚡] Checking BrowserOS runtime ({base_url})...")
            if _check_browseros_running(base_url):
                print(f"[✅] BrowserOS running at {base_url}")
                return 0
            print(f"[❌] BrowserOS not running at {base_url}")
            return 1

        if args.command == "scrape":
            return asyncio.run(
                run_scrape(
                    source=args.source,
                    limit=args.limit,
                    motor_name=args.motor,
                    portal_mode=args.mode,
                    mission_id=args.mission,
                )
            )

        parser.print_help()
        return 0
    except CliInputError as exc:
        print(f"[❌] Error: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\n[⚠️] Execution interrupted by user.")
        return 130
    except CliExecutionError as exc:
        print(f"[❌] Error: {exc}")
        return 1
    except RuntimeError as exc:
        print(f"\n[❌] Fatal Execution Error: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
