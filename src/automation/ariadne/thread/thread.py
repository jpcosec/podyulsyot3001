"""AriadneThread — mission transition graph over Labyrinth rooms.

One Thread per (portal, mission). Created only after a full successful run.
Does not know action semantics — it only remembers what was done before.
Theseus reads the Labyrinth to interpret what each action means.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.automation.contracts.motor import MotorCommand, TraceEvent
from src.automation.ariadne.thread.action import TransitionAction

DATA_ROOT = Path("data/portals")


@dataclass
class Transition:
    room_from: str
    actions: list[TransitionAction]
    room_to: str


class AriadneThread:
    """Directed graph of successful transitions for one mission."""

    def __init__(self, portal_name: str, mission_id: str) -> None:
        self.portal_name = portal_name
        self.mission_id = mission_id
        self._transitions: list[Transition] = []

    # ── Fast path ────────────────────────────────────────────────────────────

    def get_next_step(self, current_room_id: str) -> list[MotorCommand] | None:
        """Return the Motor commands for the next transition, or None if unknown."""
        for t in self._transitions:
            if t.room_from == current_room_id:
                return [cmd for action in t.actions for cmd in action.commands]
        return None

    # ── Learning ─────────────────────────────────────────────────────────────

    def add_step(self, trace_event: TraceEvent, room_after: str) -> None:
        """Record a successful transition. Called by Recorder."""
        if not trace_event.success or not trace_event.room_before:
            return
        action = TransitionAction(
            commands=(trace_event.command,),
            expected_next_room=room_after,
        )
        existing = self._find_transition(trace_event.room_before, room_after)
        if existing:
            existing.actions.append(action)
        else:
            self._transitions.append(Transition(
                room_from=trace_event.room_before,
                actions=[action],
                room_to=room_after,
            ))

    def _find_transition(self, room_from: str, room_to: str) -> Transition | None:
        return next(
            (t for t in self._transitions if t.room_from == room_from and t.room_to == room_to),
            None,
        )

    # ── Persistence ──────────────────────────────────────────────────────────

    def save(self) -> None:
        path = _thread_path(self.portal_name, self.mission_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "portal_name": self.portal_name,
            "mission_id": self.mission_id,
            "transitions": [_transition_to_dict(t) for t in self._transitions],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, portal_name: str, mission_id: str) -> "AriadneThread":
        thread = cls(portal_name, mission_id)
        path = _thread_path(portal_name, mission_id)
        if not path.exists():
            return thread
        data = json.loads(path.read_text())
        thread._transitions = [_transition_from_dict(t) for t in data.get("transitions", [])]
        return thread


# ── Serialization helpers ─────────────────────────────────────────────────────

def _transition_to_dict(t: Transition) -> dict:
    return {
        "room_from": t.room_from,
        "room_to": t.room_to,
        "actions": [
            {"commands": [{"operation": c.operation, "selector": c.selector, "value": c.value, "wait_for": c.wait_for} for c in a.commands]}
            for a in t.actions
        ],
    }


def _transition_from_dict(data: dict) -> Transition:
    actions = [
        TransitionAction(commands=tuple(
            MotorCommand(operation=c["operation"], selector=c["selector"], value=c.get("value"), wait_for=c.get("wait_for"))
            for c in a["commands"]
        ))
        for a in data.get("actions", [])
    ]
    return Transition(room_from=data["room_from"], actions=actions, room_to=data["room_to"])


def _thread_path(portal_name: str, mission_id: str) -> Path:
    return DATA_ROOT / portal_name / "threads" / f"{mission_id}.json"
