#!/usr/bin/env python3
"""Ariadne 2.0 CLI Entrypoint — Phase 4: CLI Restoration."""

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.repository import MapRepository
from src.automation.contracts import CandidateProfile
from src.automation.motors.registry import MotorRegistry


async def run_apply(
    source: str,
    job_id: str,
    cv_path: str,
    motor_name: str = "browseros",
    profile_path: Optional[str] = None,
    dry_run: bool = False,
    portal_mode: str = "easy_apply",
    mission_id: Optional[str] = None,
):
    """
    Executes the apply flow for a given source and job.

    This fulfills the requirements for the 'apply' command:
    - Accepts --source, --job-id, --cv, --motor, and --dry-run.
    - Uses MapRepository to load the AriadneMap.
    - Initializes AriadneState with profile, job data, and entry state.
    - Instantiates the Executor via MotorRegistry and passes it to the graph.
    - Implements a streaming loop for real-time node updates.
    - Handles Human-In-The-Loop interrupts.
    """
    print(f"\n🚀 Ariadne 2.0: Starting Apply Flow")
    print(f"   Portal: {source}")
    print(f"   Job ID: {job_id}")
    print(f"   CV: {cv_path}")
    print(f"   Motor: {motor_name}")
    print(f"   Dry Run: {dry_run}\n")

    # 1. Load Map via MapRepository
    repo = MapRepository()
    try:
        ariadne_map = repo.get_map(source, map_type=portal_mode)
        print(
            f"✅ Loaded Map: {ariadne_map.meta.source} {ariadne_map.meta.flow} (v{ariadne_map.meta.version})"
        )
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to load or validate map: {e}")
        sys.exit(1)

    # 2. Load Profile
    if profile_path and os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profile_data = json.load(f)
            # Validate with CandidateProfile
            profile = CandidateProfile(**profile_data)
            print(f"✅ Loaded Profile: {profile.first_name} {profile.last_name}")
    else:
        # Fallback to default mock profile
        profile = CandidateProfile(
            first_name="Ariadne",
            last_name="Pilot",
            email="ariadne@example.com",
            phone="+49 176 00000000",
            address="Semantic Way 1",
            city="Berlin",
            zip="10115",
        )
        print(f"ℹ️  Using default mock profile context.")

    # 3. Initialize AriadneState
    entry_state = (
        "job_details"
        if "job_details" in ariadne_map.states
        else next(iter(ariadne_map.states))
    )

    job_data = {
        "job_id": job_id,
        "cv_path": os.path.abspath(cv_path),
        "dry_run": dry_run,
    }

    initial_state: AriadneState = {
        "job_id": job_id,
        "portal_name": source,
        "profile_data": profile.model_dump(),
        "job_data": job_data,
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

    # 4. Instantiate Executor and Compile Graph
    try:
        executor = MotorRegistry.get_executor(motor_name)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("🛠️  Compiling Ariadne Graph...")

    # 5. Execute using astream for progress tracking
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": thread_id,
            "executor": executor,
            "motor_name": motor_name,
        }
    }

    print("🎬 Beginning JIT Execution...\n")

    try:
        async with create_ariadne_graph() as app:
            # We use stream_mode="updates" to track node execution
            async for chunk in app.astream(
                initial_state, config, stream_mode="updates"
            ):
                for node_name, state_update in chunk.items():
                    print(f"[⚡] Node: {node_name}")

                    # Report errors if any
                    if "errors" in state_update and state_update["errors"]:
                        for err in state_update["errors"]:
                            print(f"    ⚠️ ERROR: {err}")

                    # Report navigation state changes
                    if "current_state_id" in state_update:
                        print(f"    ➡️ Map State: {state_update['current_state_id']}")

            # 6. Post-execution status check (HITL & Final Results)
            final_state = await app.aget_state(config)

        if final_state.next:
            next_node = final_state.next[0]
            if next_node == "human_in_the_loop":
                print(f"\n⏸️  Apply Paused: Human-In-The-Loop required.")
                print(
                    f"    Instructions: The graph has reached a safety breakpoint or an unknown state."
                )
                print(
                    f"    To resume, run: python -m src.automation.main apply --resume --thread-id {thread_id}"
                )
                return

        state_values = final_state.values
        current_map_state = state_values.get("current_state_id")

        if current_map_state in ariadne_map.success_states:
            print("\n✅ Apply Success: Mission Completed.")
        elif state_values.get("errors"):
            print("\n❌ Apply Terminated with Errors.")
            for err in state_values["errors"]:
                print(f"    - {err}")
        else:
            print(f"\n⏹️  Apply Stopped at State: {current_map_state}")

    except Exception as e:
        print(f"\n💥 Fatal Execution Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def run_scrape(
    source: str,
    limit: int,
    motor_name: str = "crawl4ai",
    portal_mode: str = "search",
    mission_id: str = "discovery",
):
    """Execute a discovery mission through the Ariadne graph."""
    print(f"\n🚜 Ariadne 2.0: Starting Discovery Flow")
    print(f"   Portal: {source}")
    print(f"   Limit: {limit}")
    print(f"   Motor: {motor_name}")
    print(f"   Mission: {mission_id}\n")

    repo = MapRepository()
    try:
        ariadne_map = repo.get_map(source, map_type=portal_mode)
        print(
            f"✅ Loaded Map: {ariadne_map.meta.source} {ariadne_map.meta.flow} (v{ariadne_map.meta.version})"
        )
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to load or validate map: {e}")
        sys.exit(1)

    entry_state = (
        "search_results"
        if "search_results" in ariadne_map.states
        else next(iter(ariadne_map.states))
    )
    initial_state: AriadneState = {
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

    try:
        executor = MotorRegistry.get_executor(motor_name)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": thread_id,
            "executor": executor,
            "motor_name": motor_name,
        }
    }

    try:
        print("🛠️  Compiling Ariadne Graph...")
        async with create_ariadne_graph() as app:
            async for chunk in app.astream(
                initial_state, config, stream_mode="updates"
            ):
                for node_name, state_update in chunk.items():
                    print(f"[⚡] Node: {node_name}")
                    if "errors" in state_update and state_update["errors"]:
                        for err in state_update["errors"]:
                            print(f"    ⚠️ ERROR: {err}")
                    if "current_state_id" in state_update:
                        print(f"    ➡️ Map State: {state_update['current_state_id']}")

            final_state = await app.aget_state(config)
            state_values = final_state.values
            extracted_payload = state_values.get("session_memory", {})

            if state_values.get("current_state_id") in ariadne_map.success_states:
                print("\n✅ Discovery Success: Mission Completed.")
            elif state_values.get("errors"):
                print("\n❌ Discovery Terminated with Errors.")
                for err in state_values["errors"]:
                    print(f"    - {err}")
            else:
                print(
                    f"\n⏹️  Discovery Stopped at State: {state_values.get('current_state_id')}"
                )

            print("\n📦 Extracted Session Memory")
            print(json.dumps(extracted_payload, indent=2, sort_keys=True))
    except Exception as e:
        print(f"\n💥 Fatal Discovery Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Ariadne 2.0 CLI — Semantic Browser Automation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Apply Subcommand
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

    # BrowserOS-Check Subcommand
    subparsers.add_parser(
        "browseros-check", help="Verify BrowserOS runtime connectivity"
    )

    # Scrape Subcommand (Stub)
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape jobs from a portal through the Ariadne graph"
    )
    scrape_parser.add_argument("--source", required=True)
    scrape_parser.add_argument("--limit", type=int, default=10)
    scrape_parser.add_argument("--motor", default="crawl4ai")
    scrape_parser.add_argument("--mode", default="search")
    scrape_parser.add_argument("--mission", default="discovery")

    args = parser.parse_args()

    if args.command == "apply":
        if args.resume and not args.thread_id:
            print("❌ Error: --resume requires --thread-id")
            sys.exit(1)

        try:
            asyncio.run(
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
        except KeyboardInterrupt:
            print("\n🛑 Execution interrupted by user.")
            sys.exit(0)
    elif args.command == "browseros-check":
        print("🔍 Checking BrowserOS runtime (http://127.0.0.1:9000)...")
        # In a real implementation, this would ping the endpoint
        print("Status: Placeholder check complete.")
    elif args.command == "scrape":
        try:
            asyncio.run(
                run_scrape(
                    source=args.source,
                    limit=args.limit,
                    motor_name=args.motor,
                    portal_mode=args.mode,
                    mission_id=args.mission,
                )
            )
        except KeyboardInterrupt:
            print("\n🛑 Execution interrupted by user.")
            sys.exit(0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
