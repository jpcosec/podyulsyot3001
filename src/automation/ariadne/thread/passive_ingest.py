"""Passive recording ingest — Chrome DevTools Recorder JSON → AriadneThread.

Usage:
    import json
    from src.automation.ariadne.thread.passive_ingest import ingest

    thread = ingest(json.loads(recording_file.read_text()), "stepstone", "easy_apply")
    thread.save()  # draft=True — run once live to promote to canonical

Chrome DevTools Recorder step types handled:
  navigate → TransitionAction(navigate)
  click    → TransitionAction(click)
  change   → TransitionAction(fill)
  scroll   → PassiveAction(scroll)
  others   → skipped (timing, viewports, etc.)
"""

from __future__ import annotations

from urllib.parse import urlparse

from src.automation.contracts.motor import MotorCommand
from src.automation.ariadne.thread.thread import AriadneThread, Transition
from src.automation.ariadne.thread.action import Action, TransitionAction, PassiveAction


# ── Step-type → Action factory (module-level, no function call overhead) ───────

_OP_MAP: dict = {
    "navigate": lambda s, sel: TransitionAction(
        commands=(MotorCommand("navigate", "", value=s.get("url", "")),)
    ),
    "click":    lambda s, sel: TransitionAction(commands=(MotorCommand("click", sel),)),
    "change":   lambda s, sel: TransitionAction(
        commands=(MotorCommand("fill", sel, value=s.get("value", "")),)
    ),
    "scroll":   lambda s, sel: PassiveAction(operation="scroll"),
}


def ingest(devtools_json: dict, portal_name: str, mission_id: str) -> AriadneThread:
    """Parse a Chrome DevTools Recorder JSON and return a draft AriadneThread."""
    thread = AriadneThread(portal_name, mission_id)
    thread.draft = True
    _process_steps(thread, devtools_json.get("steps", []))
    return thread


def _process_steps(thread: AriadneThread, steps: list) -> None:
    current_room, pending = "start", []
    for step in steps:
        action = _map_step(step)
        if action is None:
            continue
        if step.get("type") == "navigate":
            current_room, pending = _commit_navigate(thread, current_room, pending, action, step)
        else:
            pending.append(action)
    if pending:
        thread._transitions.append(Transition(current_room, pending, current_room + ".end"))


def _commit_navigate(thread, room_from, pending, nav_action, step) -> tuple:
    next_room = _url_to_room_id(step.get("url", ""))
    thread._transitions.append(Transition(room_from, pending + [nav_action], next_room))
    return next_room, []


def _map_step(step: dict) -> Action | None:
    handler = _OP_MAP.get(step.get("type"))
    if not handler:
        return None
    return handler(step, _best_selector(step.get("selectors", [])))


def _best_selector(selectors: list) -> str:
    for group in selectors:
        if group:
            return group[0]
    return ""


def _url_to_room_id(url: str) -> str:
    p = urlparse(url)
    slug = (p.netloc + p.path).rstrip("/").replace("/", ".").replace("-", "_")
    return slug or "home"
