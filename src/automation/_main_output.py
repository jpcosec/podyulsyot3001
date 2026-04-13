"""CLI output helpers."""


def print_apply_banner(
    source: str, job_id: str, cv_path: str, motor_name: str, dry_run: bool
) -> None:
    """Print the apply flow banner."""
    print("\n[⚡] Ariadne 2.0: Starting Apply Flow")
    print(f"   Portal: {source}")
    print(f"   Job ID: {job_id}")
    print(f"   CV: {cv_path}")
    print(f"   Motor: {motor_name}")
    print(f"   Dry Run: {dry_run}\n")


def print_scrape_banner(
    source: str, limit: int, motor_name: str, mission_id: str
) -> None:
    """Print the scrape flow banner."""
    print("\n[⚡] Ariadne 2.0: Starting Discovery Flow")
    print(f"   Portal: {source}")
    print(f"   Limit: {limit}")
    print(f"   Motor: {motor_name}")
    print(f"   Mission: {mission_id}\n")


def print_map_loaded(ariadne_map) -> None:
    """Print the loaded map metadata."""
    print(
        f"[✅] Loaded Map: {ariadne_map.meta.source} {ariadne_map.meta.flow} (v{ariadne_map.meta.version})"
    )


def print_updates(chunk: dict) -> None:
    """Render streamed node updates for interactive CLI runs."""
    for node_name, state_update in chunk.items():
        print_node_header(node_name)
        print_node_errors(state_update)
        print_node_state(state_update)


def print_node_header(node_name: str) -> None:
    """Print the current graph node name."""
    print(f"[⚡] Node: {node_name}")


def print_node_errors(state_update: dict) -> None:
    """Print node errors."""
    for err in state_update.get("errors", []):
        print(f"    [⚠️] ERROR: {err}")


def print_node_state(state_update: dict) -> None:
    """Print the active map state when present."""
    if "current_state_id" in state_update:
        print(f"    [⚡] Map State: {state_update['current_state_id']}")


def print_hitl_resume(thread_id: str) -> int:
    """Print HITL resume message and return exit code."""
    print(f"\n[⏸️] Session paused at breakpoint. Thread ID: {thread_id}")
    print("   Resume with: ariadne --resume --thread-id {thread_id}")
    return 0


def print_success(flow: str) -> int:
    """Print success message and return exit code."""
    print(f"\n[✅] {flow} completed successfully!")
    return 0


def print_errors(flow: str, errors: list) -> int:
    """Print errors and return exit code."""
    print(f"\n[❌] {flow} failed with errors:")
    for err in errors:
        print(f"   - {err}")
    return 1


def print_stopped(flow: str, state_id: str | None) -> int:
    """Print stopped message and return exit code."""
    print(f"\n[⏹️] {flow} stopped at state: {state_id or 'unknown'}")
    return 0


def print_scrape_status(state_values: dict, ariadne_map) -> str:
    """Print and return scrape status."""
    current_state = state_values.get("current_state_id", "unknown")
    if current_state in ariadne_map.success_states:
        status = "[✅] Discovery complete"
    elif state_values.get("errors"):
        status = "[❌] Discovery failed"
    else:
        status = "[⏹️] Discovery stopped"
    print(f"   Status: {status} (state: {current_state})")
    return status


def print_browseros_check_result(is_healthy: bool, base_url: str) -> int:
    """Print the BrowserOS health result."""
    if is_healthy:
        print(f"[✅] BrowserOS running at {base_url}")
        return 0
    print(f"[❌] BrowserOS not running at {base_url}")
    return 1


def handle_cli_error(message: str, code: int = 1) -> int:
    """Print a CLI error message and return the exit code."""
    print(message)
    return code
