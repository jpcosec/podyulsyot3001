"""Automation entrypoint.

Usage:
    python -m src.automation.main <portal>/<mission> [--appimage PATH] [--compile]

The --compile flag runs the mission via compiled C4AScript (Level 0).
On failure it degrades automatically to Level 1 (LangGraph).

Example:
    python -m src.automation.main stepstone/easy_apply --compile
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
    parser.add_argument("--compile", action="store_true", help="Run via C4AScript (Level 0); degrades to LangGraph on failure")
    return parser.parse_args()


async def _run(instruction: str, appimage: str | None, use_compile: bool = False) -> None:
    session_id = str(uuid.uuid4())
    portal, mission = _split_instruction(instruction)

    async with BrowserOSAdapter(session_id=session_id, appimage_path=appimage) as adapter:
        if use_compile:
            result = await _run_compiled(adapter, portal, mission, instruction)
        else:
            graph = build_graph(adapter, adapter, portal, mission)
            result = await graph.ainvoke({"instruction": instruction})

    _print_result(result)


async def _run_compiled(adapter, portal: str, mission: str, instruction: str) -> dict:
    """Try C4AScript (Level 0); degrade to LangGraph (Level 1) on any error."""
    try:
        return await _run_c4a(adapter, portal, mission)
    except Exception as exc:
        print(f"[⬇️]  C4AScript failed ({exc}), degrading to LangGraph")
        graph = build_graph(adapter, adapter, portal, mission)
        return await graph.ainvoke({"instruction": instruction})


async def _run_c4a(adapter, portal: str, mission: str) -> dict:
    from crawl4ai import CrawlerRunConfig
    from src.automation.ariadne.thread.thread import AriadneThread
    from src.automation.ariadne.thread.compiler import compile as compile_thread

    thread = AriadneThread.load(portal, mission)
    script = compile_thread(thread)
    url = await adapter._resolve_url()
    config = CrawlerRunConfig(c4a_script=script)
    result = await adapter._crawler.arun(url, config=config)
    if not result.success:
        raise RuntimeError(result.error_message or "C4AScript returned failure")
    return {"is_mission_complete": True, "current_room_id": None, "c4a_output": result.cleaned_html}


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
    asyncio.run(_run(args.instruction, args.appimage, args.compile))


if __name__ == "__main__":
    main()
