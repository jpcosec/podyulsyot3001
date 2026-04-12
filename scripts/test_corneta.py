#!/usr/bin/env python3
"""
Test Corneta: Verifies Ariadne 2.0 fallback cascade.

Usage:
    python scripts/test_corneta.py

Auto-loads: .env via src.automation.ariadne.config
"""

import asyncio
import uuid

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


async def run_test():
    print("\n[🚀] Test Corneta: LLM auto-discovery + HITL fallback")
    print("[💡] Task: Find the main heading on example.com")
    print("[🔑] Key: No pre-defined map exists -> should hit LLM\n")

    thread_id = str(uuid.uuid4())

    initial_state = {
        "job_id": "test_corneta",
        "portal_name": "example",
        "profile_data": {},
        "job_data": {"task": "Find the main heading text"},
        "path_id": "explore",
        "current_mission_id": "explore_heading",
        "current_state_id": "start",
        "current_url": "https://example.com",
        "dom_elements": [],
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "example",
        "patched_components": {},
    }

    executor = Crawl4AIExecutor()

    config = {
        "configurable": {
            "thread_id": thread_id,
            "executor": executor,
            "motor_name": "crawl4ai",
            "record_graph": True,
            "recording_dir": "data/ariadne/recordings",
        }
    }

    print(f"[⚡] Thread ID: {thread_id}")
    print("[⚡] Running exploration (no map exists)...\n")

    async with executor:
        async with create_ariadne_graph(use_memory=True) as app:
            try:
                async for event in app.astream(
                    initial_state, config, stream_mode="updates"
                ):
                    if isinstance(event, dict):
                        for node, state_update in event.items():
                            if not isinstance(state_update, dict):
                                continue
                            print(f"\n[->] {node.upper()}")
                            if state_update.get("errors"):
                                print(f"     [x] {state_update['errors']}")
                            mem = state_update.get("session_memory", {})
                            if mem.get("human_intervention"):
                                print(f"     [!] HITL triggered")
            except Exception as e:
                print(f"\n[!!] Breakpoint reached: {type(e).__name__}")

            final_state = await app.aget_state(config)

            print("\n" + "=" * 50)
            print("[RESULT]")
            print("=" * 50)

            if final_state.next and final_state.next[0] == "human_in_the_loop":
                print("[PASS] HITL reached (LLM failed -> human called)")
                return True
            else:
                print(f"[INFO] Next: {final_state.next}")
                return False


if __name__ == "__main__":
    result = asyncio.run(run_test())
    exit(0 if result else 1)
