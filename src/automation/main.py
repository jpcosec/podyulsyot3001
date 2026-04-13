#!/usr/bin/env python3
"""CLI entrypoint for Ariadne browser automation flows."""

from __future__ import annotations

import asyncio
import os
import traceback
import sys

from src.automation._main_parsing import build_parser
from src.automation._main_config import (
    CliInputError,
    CliExecutionError,
    load_profile,
    load_map,
    get_adapter,
)
from src.automation._main_state import build_apply_state, build_scrape_state
from src.automation._main_runtime import prepare_runtime_config
from src.automation._main_output import (
    print_apply_banner,
    print_scrape_banner,
    print_map_loaded,
    print_hitl_resume,
    print_success,
    print_errors,
    print_stopped,
    print_scrape_status,
    print_browseros_check_result,
    handle_cli_error,
)
from src.automation._main_dispatch import (
    dispatch_command,
    run_apply_command,
    run_scrape_command,
    run_browseros_check,
)


async def run_apply(
    source: str,
    job_id: str,
    cv_path: str,
    motor_name: str,
    profile_path: str | None,
    dry_run: bool,
    portal_mode: str,
    mission_id: str | None,
) -> int:
    """Execute an apply flow."""
    profile = load_profile(profile_path)
    ariadne_map = await load_map(source, portal_mode)
    print_apply_banner(source, job_id, cv_path, motor_name, dry_run)
    print_map_loaded(ariadne_map)

    adapter = get_adapter(motor_name)
    thread_id, config, theseus = await prepare_runtime_config(
        adapter, motor_name, source, portal_mode, mission_id
    )

    initial_state = build_apply_state(
        source, job_id, cv_path, profile, ariadne_map, dry_run, portal_mode, mission_id
    )

    print("[⚡] Compiling Ariadne Graph...")

    async with adapter as active_adapter:
        config["configurable"]["executor"] = active_adapter
        final_state = await theseus.run(initial_state, config)

    state_values = final_state.values
    if is_hitl_pause(final_state):
        return print_hitl_resume(thread_id)
    if is_success_state(state_values, ariadne_map):
        return print_success("Apply")
    if state_values.get("errors"):
        return print_errors("Apply", state_values["errors"])
    return print_stopped("Apply", state_values.get("current_state_id"))


async def run_scrape(
    source: str,
    limit: int,
    motor_name: str,
    portal_mode: str,
    mission_id: str,
) -> int:
    """Execute a scrape flow."""
    ariadne_map = await load_map(source, portal_mode)
    print_scrape_banner(source, limit, motor_name, mission_id)
    print_map_loaded(ariadne_map)

    adapter = get_adapter(motor_name)
    _, config, theseus = await prepare_runtime_config(
        adapter, motor_name, source, portal_mode, mission_id
    )

    initial_state = build_scrape_state(
        source, limit, ariadne_map, portal_mode, mission_id
    )

    print("[⚡] Compiling Ariadne Graph...")

    async with adapter as active_adapter:
        config["configurable"]["executor"] = active_adapter
        final_state = await theseus.run(initial_state, config)

    return handle_scrape_result(final_state, ariadne_map)


def is_hitl_pause(state) -> bool:
    """Check if state is at HITL pause."""
    session_memory = state.values.get("session_memory", {})
    return session_memory.get("human_intervention")


def is_success_state(state_values: dict, ariadne_map) -> bool:
    """Check if current state is a success state."""
    current = state_values.get("current_state_id")
    return current in ariadne_map.success_states


def handle_scrape_result(final_state, ariadne_map) -> int:
    """Render the scrape result and return the CLI exit code."""
    state_values = final_state.values
    print_scrape_status(state_values, ariadne_map)
    print("\n[📦] Extracted Session Memory")
    for key, value in state_values.get("session_memory", {}).items():
        print(f"   {key}: {value}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args, dispatch commands, and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    base_url = os.environ.get("BROWSEROS_BASE_URL", "http://127.0.0.1:9000")

    commands = {
        "apply": lambda: run_apply_command(args, run_apply),
        "browseros-check": lambda: run_browseros_check(
            base_url, get_adapter, print_browseros_check_result
        ),
        "scrape": lambda: run_scrape_command(args, run_scrape),
    }

    try:
        return dispatch_command(args, base_url, parser, commands)
    except CliInputError as exc:
        return handle_cli_error(f"[❌] Error: {exc}")
    except KeyboardInterrupt:
        return handle_cli_error("\n[⚠️] Execution interrupted by user.", 130)
    except CliExecutionError as exc:
        return handle_cli_error(f"[❌] Error: {exc}")
    except RuntimeError as exc:
        return handle_cli_error(
            f"\n[❌] Fatal Execution Error: {exc}\n{traceback.format_exc()}"
        )


if __name__ == "__main__":
    sys.exit(main())
