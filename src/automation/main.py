"""Automation entrypoint.

Usage:
    python -m src.automation.main <portal>/<mission> [--appimage PATH]

Example:
    python -m src.automation.main stepstone/easy_apply
"""

from __future__ import annotations

import argparse
import asyncio
import os
import uuid

from dotenv import load_dotenv

from src.automation.adapters.browser_os import BrowserOSAdapter
from src.automation.langgraph.builder import build_graph

load_dotenv()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an Ariadne automation mission.")
    parser.add_argument("instruction", help="portal/mission, e.g. stepstone/easy_apply")
    parser.add_argument("--appimage", default=os.getenv("BROWSEROS_APPIMAGE_PATH"), help="Path to BrowserOS AppImage")
    return parser.parse_args()


async def _run(instruction: str, appimage: str | None) -> None:
    session_id = str(uuid.uuid4())
    portal, mission = _split_instruction(instruction)

    async with BrowserOSAdapter(session_id=session_id, appimage_path=appimage) as adapter:
        graph = build_graph(adapter, adapter, portal, mission)
        result = await graph.ainvoke({"instruction": instruction})

    _print_result(result)


def _split_instruction(instruction: str) -> tuple[str, str]:
    parts = instruction.strip().split("/", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "default")


def _print_result(state: dict) -> None:
    print(f"[✅] complete={state.get('is_mission_complete')}")
    print(f"[📍] room={state.get('current_room_id')}")
    if state.get("errors"):
        print(f"[⚠️]  errors={state['errors']}")
    if state.get("extracted_data"):
        print(f"[📦] extracted={len(state['extracted_data'])} items")


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args.instruction, args.appimage))


if __name__ == "__main__":
    main()
