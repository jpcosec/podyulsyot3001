# CLI Rewrite: Universal Agnostic Entrypoint

**Explanation:** Replace domain-specific `apply`/`scrape` subcommands with a single universal command `instruction + --portal + kwargs`. The CLI should be dumb — business logic belongs in the graph.

**Reference:** `src/automation/main.py`

**Status:** Not started.

**Why it's wrong:** `main.py` has `apply`, `scrape`, `browseros-check` subcommands with job-specific flags (`--cv`, `--job-id`). This couples the transport layer (CLI) to a specific domain (job applications). Dead code block at lines 382–396 (`_ensure_browseros` after `raise`). `run_apply` and `run_scrape` duplicate graph-wiring logic.

**Real fix:**
1. Delete `_build_apply_state`, `_build_scrape_state`, `run_apply`, `run_scrape`.
2. Replace `_build_parser()` with a single-command parser: `instruction` (positional), `--portal` (required), `--motor`, `kwargs` (nargs=*).
3. Implement `parse_kwargs(kwarg_list) -> dict` to convert `key=value` strings.
4. Single `run_ariadne(args)` function that builds minimal initial state and wraps execution in `async with executor` + `async with create_ariadne_graph()`.
5. Remove dead code block at lines 382–396.

**Don't:** Reconstruct `apply`/`scrape` as wrappers — they must be deleted entirely.

**Steps:**
1. Write new `_build_parser()`.
2. Write `parse_kwargs()`.
3. Write `run_ariadne()` with universal initial state.
4. Delete all domain-specific functions.
5. Run `python -m pytest tests/unit/automation/ -q` to verify nothing breaks.
6. Manual smoke test: `python -m src.automation.main "easy_apply" --portal linkedin url=https://example.com`.

**Reference implementation:**

```python
#!/usr/bin/env python3
"""Ariadne 2.0 CLI - Universal Entrypoint"""

import argparse
import asyncio
import json
import os
import uuid
import traceback

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.registry import MotorRegistry


def parse_kwargs(kwarg_list: list[str]) -> dict:
    """Converts ['job_id=123', 'limit=10'] into {'job_id': '123', 'limit': '10'}"""
    return dict(item.split("=", 1) for item in kwarg_list if "=" in item)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ariadne 2.0 - Semantic Browser")
    parser.add_argument("instruction", help="Natural language intent or mission ID")
    parser.add_argument("--portal", required=True, help="Portal name (e.g. linkedin, stepstone)")
    parser.add_argument("--motor", default="crawl4ai", help="Execution motor")
    parser.add_argument("kwargs", nargs="*", help="Dynamic key=value context (e.g. url=... cv_path=...)")
    return parser


async def run_ariadne(args) -> int:
    context_data = parse_kwargs(args.kwargs)
    thread_id = str(uuid.uuid4())

    profile_data = {}
    if "profile" in context_data and os.path.exists(context_data["profile"]):
        with open(context_data["profile"], "r", encoding="utf-8") as f:
            profile_data = json.load(f)

    initial_state = {
        "instruction": args.instruction,
        "portal_name": args.portal,
        "job_id": context_data.get("job_id", f"session-{thread_id[:8]}"),
        "current_url": context_data.get("url", ""),
        "session_memory": context_data,
        "profile_data": profile_data,
        "job_data": context_data,  # for {{job_data.cv_path}} placeholders
        "dom_elements": [],
        "errors": [],
        "history": [],
        "portal_mode": args.portal,
        "patched_components": {},
    }

    try:
        executor = MotorRegistry.get_executor(args.motor)
    except ValueError as e:
        print(f"[❌] Error: {e}")
        return 1

    config = {
        "configurable": {
            "thread_id": thread_id,
            "executor": executor,
            "motor_name": args.motor,
            "record_graph": True,
        }
    }

    print(f"\n[🚀] Ariadne: '{args.instruction}' on {args.portal}")

    try:
        async with executor as active_executor:
            config["configurable"]["executor"] = active_executor
            async with create_ariadne_graph() as app:
                async for chunk in app.astream(initial_state, config, stream_mode="updates"):
                    for node_name, state_update in chunk.items():
                        print(f"  [⚡] Node: {node_name}")
                        if state_update.get("errors"):
                            print(f"       [⚠️] Errors: {state_update['errors']}")
                        if "current_state_id" in state_update:
                            print(f"       [📍] State: {state_update['current_state_id']}")

                final_state = await app.aget_state(config)
                if final_state.next and final_state.next[0] == "human_in_the_loop":
                    print(f"\n[🛑] HUMAN PAUSE. Resume with thread: {thread_id}")
                else:
                    print("\n[✅] MISSION COMPLETE")
                    if final_state.values.get("session_memory"):
                        print("[📦] Final memory:", json.dumps(final_state.values["session_memory"], indent=2))
        return 0
    except Exception as e:
        print(f"\n[❌] Fatal: {e}")
        traceback.print_exc()
        return 1


def main():
    parser = _build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_ariadne(args)))


if __name__ == "__main__":
    main()
```
