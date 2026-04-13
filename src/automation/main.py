#!/usr/bin/env python3
"""CLI entrypoint for Ariadne browser automation flows."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import traceback
import uuid
from typing import Optional

from src.automation.ariadne.core.actors import Theseus
from src.automation.ariadne.core.cognition import AriadneThread, Labyrinth
from src.automation.ariadne.models import AriadneMap, AriadneState
from src.automation.ariadne.repository import MapRepository
from src.automation.contracts import CandidateProfile
from src.automation.motors.registry import MotorRegistry


class CliInputError(ValueError):
    """Raised when CLI inputs are invalid before execution starts."""


class CliExecutionError(RuntimeError):
    """Raised when a CLI flow cannot be started or completed."""


def _add_apply_args(parser):
    """Add arguments for apply command."""
    parser.add_argument("--source", required=True, help="Portal source (e.g., linkedin, stepstone)")
    parser.add_argument("--job-id", required=True, help="Job ID to apply to")
    parser.add_argument("--cv", required=True, help="Path to CV file")
    parser.add_argument("--motor", default="browseros", help="Execution motor (browseros, crawl4ai)")
    parser.add_argument("--profile", help="Path to profile JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Run without final submission")
    parser.add_argument("--mode", default="easy_apply", help="Portal mode to use (default: easy_apply)")
    parser.add_argument("--mission", help="Mission id to filter eligible edges")
    parser.add_argument("--resume", action="store_true", help="Resume a paused session")
    parser.add_argument("--thread-id", help="Thread ID to resume")


def _configure_apply_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the apply command."""
    apply_parser = subparsers.add_parser("apply", help="Execute an Ariadne apply flow")
    _add_apply_args(apply_parser)


def _configure_scrape_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the scrape command."""
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape jobs from a portal through the Ariadne graph"
    )
    scrape_parser.add_argument("--source", required=True)
    scrape_parser.add_argument("--limit", type=int, default=10)
    scrape_parser.add_argument("--motor", default="crawl4ai")
    scrape_parser.add_argument("--mode", default="search")
    scrape_parser.add_argument("--mission", default="discovery")


def _build_parser() -> argparse.ArgumentParser:
    """Build the canonical automation CLI parser."""
    parser = argparse.ArgumentParser(
        description="Ariadne 2.0 CLI - Semantic Browser Automation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    _configure_apply_parser(subparsers)
    subparsers.add_parser(
        "browseros-check", help="Verify BrowserOS runtime connectivity"
    )
    _configure_scrape_parser(subparsers)
    return parser


def _default_profile() -> CandidateProfile:
    """Return a deterministic fallback profile for local runs."""
    defaults = {
        "first_name": "Ariadne",
        "last_name": "Pilot",
        "email": "ariadne@example.com",
        "phone": "+49 176 00000000",
        "address": "Semantic Way 1",
        "city": "Berlin",
        "zip": "10115",
    }
    return CandidateProfile(**defaults)


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


def _adapter_kwargs(motor_name: str) -> dict:
    """Build backend-specific adapter kwargs from the environment."""
    if motor_name != "browseros":
        return {}
    return {
        "base_url": os.environ.get("BROWSEROS_BASE_URL", "http://127.0.0.1:9000"),
        "appimage_path": os.environ.get("BROWSEROS_APPIMAGE_PATH"),
    }


def _get_adapter(motor_name: str):
    """Resolve a browser adapter instance from the motor registry."""
    try:
        return MotorRegistry.get_adapter(motor_name, **_adapter_kwargs(motor_name))
    except ValueError as exc:
        raise CliInputError(str(exc)) from exc


def _build_config(
    adapter,
    motor_name: str,
    thread_id: str,
    labyrinth: Labyrinth | None = None,
    ariadne_thread: AriadneThread | None = None,
) -> dict:
    """Build a shared graph execution config."""
    return {
        "configurable": {
            "thread_id": thread_id,
            "executor": adapter,
            "motor_name": motor_name,
            "record_graph": True,
            "labyrinth": labyrinth,
            "ariadne_thread": ariadne_thread,
        }
    }


def _build_theseus(
    adapter,
    labyrinth: Labyrinth,
    ariadne_thread: AriadneThread,
) -> Theseus:
    """Build the mission coordinator."""
    return Theseus(adapter, adapter, labyrinth, ariadne_thread)


def _print_updates(chunk: dict) -> None:
    """Render streamed node updates for interactive CLI runs."""
    for node_name, state_update in chunk.items():
        _print_node_header(node_name)
        _print_node_errors(state_update)
        _print_node_state(state_update)


def _print_node_header(node_name: str) -> None:
    """Print the current graph node name."""
    print(f"[⚡] Node: {node_name}")


def _print_node_errors(state_update: dict) -> None:
    """Print node errors."""
    for err in state_update.get("errors", []):
        print(f"    [⚠️] ERROR: {err}")


def _print_node_state(state_update: dict) -> None:
    """Print the active map state when present."""
    if "current_state_id" in state_update:
        print(f"    [⚡] Map State: {state_update['current_state_id']}")





async def _load_runtime_cognition(
    source: str,
    portal_mode: str,
    mission_id: Optional[str],
) -> tuple[Labyrinth, AriadneThread]:
    """Load runtime cognition objects for the active portal and mission."""
    labyrinth = await Labyrinth.load_from_db(source, map_type=portal_mode)
    ariadne_thread = await AriadneThread.load_from_db(
        source,
        mission_id=mission_id,
        map_type=portal_mode,
    )
    return labyrinth, ariadne_thread


def _print_apply_banner(
    source: str,
    job_id: str,
    cv_path: str,
    motor_name: str,
    dry_run: bool,
) -> None:
    """Print the apply flow banner."""
    print("\n[⚡] Ariadne 2.0: Starting Apply Flow")
    print(f"   Portal: {source}")
    print(f"   Job ID: {job_id}")
    print(f"   CV: {cv_path}")
    print(f"   Motor: {motor_name}")
    print(f"   Dry Run: {dry_run}\n")


def _print_scrape_banner(
    source: str,
    limit: int,
    motor_name: str,
    mission_id: str,
) -> None:
    """Print the scrape flow banner."""
    print("\n[⚡] Ariadne 2.0: Starting Discovery Flow")
    print(f"   Portal: {source}")
    print(f"   Limit: {limit}")
    print(f"   Motor: {motor_name}")
    print(f"   Mission: {mission_id}\n")


def _print_map_loaded(ariadne_map: AriadneMap) -> None:
    """Print the loaded map metadata."""
    print(
        f"[✅] Loaded Map: {ariadne_map.meta.source} {ariadne_map.meta.flow} (v{ariadne_map.meta.version})"
    )


async def _prepare_runtime_config(
    adapter,
    motor_name: str,
    source: str,
    portal_mode: str,
    mission_id: Optional[str],
) -> tuple[str, dict, Theseus]:
    """Build runtime config and the mission coordinator."""
    labyrinth, ariadne_thread = await _load_runtime_cognition(
        source,
        portal_mode,
        mission_id,
    )
    thread_id = str(uuid.uuid4())
    config = _build_config(adapter, motor_name, thread_id, labyrinth, ariadne_thread)
    return thread_id, config, _build_theseus(adapter, labyrinth, ariadne_thread)


def _get_entry_state(ariadne_map: AriadneMap, preferred: str) -> str:
    """Resolve the entry state from map states."""
    return preferred if preferred in ariadne_map.states else next(iter(ariadne_map.states))


def _base_state(
    portal_name: str,
    mission_id: str,
    entry_state: str,
    portal_mode: str,
    profile_data: dict,
    job_data: dict,
    session_memory: dict,
) -> dict:
    """Build base state structure shared by apply and scrape."""
    return {
        "portal_name": portal_name,
        "current_mission_id": mission_id,
        "current_state_id": entry_state,
        "profile_data": profile_data,
        "job_data": job_data,
        "path_id": str(uuid.uuid4()),
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": session_memory,
        "errors": [],
        "history": [],
        "portal_mode": portal_mode,
        "patched_components": {},
    }


def _apply_job_data(job_id: str, cv_path: str, dry_run: bool) -> dict:
    """Build job data for apply flow."""
    return {
        "job_id": job_id,
        "cv_path": os.path.abspath(cv_path),
        "dry_run": dry_run,
    }


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
    entry_state = _get_entry_state(ariadne_map, "job_details")
    state = _base_state(
        portal_name=source,
        mission_id=mission_id or portal_mode,
        entry_state=entry_state,
        portal_mode=portal_mode,
        profile_data=profile.model_dump(),
        job_data=_apply_job_data(job_id, cv_path, dry_run),
        session_memory={},
    )
    state["job_id"] = job_id
    return state


def _scrape_job_data(limit: int) -> dict:
    """Build job data for scrape flow."""
    return {"limit": limit}


def _scrape_session_memory(limit: int) -> dict:
    """Build session memory for scrape flow."""
    return {"limit": limit}


def _build_scrape_state(
    source: str,
    limit: int,
    ariadne_map: AriadneMap,
    portal_mode: str,
    mission_id: str,
) -> AriadneState:
    """Construct the initial state for a scrape run."""
    entry_state = _get_entry_state(ariadne_map, "search_results")
    state = _base_state(
        portal_name=source,
        mission_id=mission_id,
        entry_state=entry_state,
        portal_mode=portal_mode,
        profile_data={},
        job_data=_scrape_job_data(limit),
        session_memory=_scrape_session_memory(limit),
    )
    state["job_id"] = f"discovery-{source}-{uuid.uuid4().hex[:8]}"
    return state


async def _invoke_graph(
    theseus: Theseus,
    adapter,
    initial_state: AriadneState,
    config: dict,
):
    """Run the graph within the adapter lifecycle."""
    async with adapter as active_adapter:
        config["configurable"]["executor"] = active_adapter
        return await theseus.run(initial_state, config)


def _handle_apply_result(final_state, ariadne_map: AriadneMap, thread_id: str) -> int:
    """Render the apply result and return the CLI exit code."""
    if _is_hitl_pause(final_state):
        return _print_hitl_resume(thread_id)
    state_values = final_state.values
    if _is_success_state(state_values, ariadne_map):
        return _print_success("Apply")
    if state_values.get("errors"):
        return _print_errors("Apply", state_values["errors"])
    return _print_stopped("Apply", state_values.get("current_state_id"))


def _handle_scrape_result(final_state, ariadne_map: AriadneMap) -> int:
    """Render the scrape result and return the CLI exit code."""
    state_values = final_state.values
    extracted_payload = state_values.get("session_memory", {})

    status = _print_scrape_status(state_values, ariadne_map)
    print("\n[📦] Extracted Session Memory")
    print(json.dumps(extracted_payload, indent=2, sort_keys=True))
    return status


def _is_hitl_pause(final_state) -> bool:
    """Return whether the graph paused for human intervention."""
    return bool(final_state.next and final_state.next[0] == "human_in_the_loop")


def _print_hitl_resume(thread_id: str) -> int:
    """Print HITL resume instructions."""
    print("\n[⚠️] Apply Paused: Human-In-The-Loop required.")
    print(
        "    Instructions: The graph has reached a safety breakpoint or an unknown state."
    )
    print(
        f"    To resume, run: python -m src.automation.main apply --resume --thread-id {thread_id}"
    )
    return 0


def _is_success_state(state_values: dict, ariadne_map: AriadneMap) -> bool:
    """Return whether the current state is a success state."""
    return state_values.get("current_state_id") in ariadne_map.success_states


def _print_success(flow_name: str) -> int:
    """Print a success message for the flow."""
    print(f"\n[✅] {flow_name} Success: Mission Completed.")
    return 0


def _print_errors(flow_name: str, errors: list[str]) -> int:
    """Print flow errors and return a failing exit code."""
    print(f"\n[❌] {flow_name} Terminated with Errors.")
    for err in errors:
        print(f"    - {err}")
    return 1


def _print_stopped(flow_name: str, state_id: str | None) -> int:
    """Print a stopped-at-state message."""
    print(f"\n[⚠️] {flow_name} Stopped at State: {state_id}")
    return 0


def _print_scrape_status(state_values: dict, ariadne_map: AriadneMap) -> int:
    """Print scrape status before memory output."""
    if _is_success_state(state_values, ariadne_map):
        return _print_success("Discovery")
    if state_values.get("errors"):
        return _print_errors("Discovery", state_values["errors"])
    return _print_stopped("Discovery", state_values.get("current_state_id"))


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
    _print_apply_banner(source, job_id, cv_path, motor_name, dry_run)

    ariadne_map = _load_map(source, portal_mode)
    _print_map_loaded(ariadne_map)

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
    adapter = _get_adapter(motor_name)
    thread_id, config, theseus = await _prepare_runtime_config(
        adapter,
        motor_name,
        source,
        portal_mode,
        mission_id or portal_mode,
    )

    print("[⚡] Compiling Ariadne Graph...")
    print("[⚡] Beginning JIT Execution...\n")

    final_state = await _invoke_graph(theseus, adapter, initial_state, config)
    return _handle_apply_result(final_state, ariadne_map, thread_id)


async def run_scrape(
    source: str,
    limit: int,
    motor_name: str = "crawl4ai",
    portal_mode: str = "search",
    mission_id: str = "discovery",
) -> int:
    """Execute a discovery mission through the Ariadne graph."""
    _print_scrape_banner(source, limit, motor_name, mission_id)

    ariadne_map = _load_map(source, portal_mode)
    _print_map_loaded(ariadne_map)

    initial_state = _build_scrape_state(
        source, limit, ariadne_map, portal_mode, mission_id
    )
    adapter = _get_adapter(motor_name)
    _, config, theseus = await _prepare_runtime_config(
        adapter,
        motor_name,
        source,
        portal_mode,
        mission_id,
    )

    print("[⚡] Compiling Ariadne Graph...")

    final_state = await _invoke_graph(theseus, adapter, initial_state, config)
    return _handle_scrape_result(final_state, ariadne_map)


def _extract_apply_args(args) -> dict:
    """Extract apply arguments from CLI args."""
    return {
        "source": args.source,
        "job_id": args.job_id,
        "cv_path": args.cv,
        "motor_name": args.motor,
        "profile_path": args.profile,
        "dry_run": args.dry_run,
        "portal_mode": args.mode,
        "mission_id": args.mission,
    }


def _run_apply_command(args) -> int:
    """Run the apply command from parsed CLI args."""
    if args.resume and not args.thread_id:
        raise CliInputError("--resume requires --thread-id")
    return asyncio.run(run_apply(**_extract_apply_args(args)))


def _run_browseros_check(base_url: str) -> int:
    """Check BrowserOS runtime health."""
    print(f"[⚡] Checking BrowserOS runtime ({base_url})...")
    adapter = _get_adapter("browseros")
    return _print_browseros_check_result(asyncio.run(adapter.is_healthy()), base_url)


def _print_browseros_check_result(is_healthy: bool, base_url: str) -> int:
    """Print the BrowserOS health result."""
    if is_healthy:
        print(f"[✅] BrowserOS running at {base_url}")
        return 0
    print(f"[❌] BrowserOS not running at {base_url}")
    return 1


def _extract_scrape_args(args) -> dict:
    """Extract scrape arguments from CLI args."""
    return {
        "source": args.source,
        "limit": args.limit,
        "motor_name": args.motor,
        "portal_mode": args.mode,
        "mission_id": args.mission,
    }


def _run_scrape_command(args) -> int:
    """Run the scrape command from parsed CLI args."""
    return asyncio.run(run_scrape(**_extract_scrape_args(args)))


def _dispatch_command(args, base_url: str, parser: argparse.ArgumentParser) -> int:
    """Dispatch the parsed CLI command."""
    command_handlers = {
        "apply": lambda: _run_apply_command(args),
        "browseros-check": lambda: _run_browseros_check(base_url),
        "scrape": lambda: _run_scrape_command(args),
    }
    handler = command_handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 0
    return handler()


def _handle_cli_error(message: str, code: int = 1) -> int:
    """Print a CLI error message and return the exit code."""
    print(message)
    return code


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args, dispatch commands, and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    base_url = os.environ.get("BROWSEROS_BASE_URL", "http://127.0.0.1:9000")

    try:
        return _dispatch_command(args, base_url, parser)
    except CliInputError as exc:
        return _handle_cli_error(f"[❌] Error: {exc}")
    except KeyboardInterrupt:
        return _handle_cli_error("\n[⚠️] Execution interrupted by user.", 130)
    except CliExecutionError as exc:
        return _handle_cli_error(f"[❌] Error: {exc}")
    except RuntimeError as exc:
        _handle_cli_error(f"\n[❌] Fatal Execution Error: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
