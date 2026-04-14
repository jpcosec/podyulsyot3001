"""Action taxonomy — everything that can happen on a page.

PassiveAction    → no DOM effect (hover, scroll)
ExtractionAction → reads DOM, returns data, no structural change
TransitionAction → mutates the Skeleton, generates Thread edges

Only TransitionAction creates new rooms in the Labyrinth and edges in the Thread.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.automation.contracts.motor import MotorCommand


@dataclass(frozen=True)
class PassiveAction:
    type: Literal["passive"] = field(default="passive", init=False)
    operation: Literal["scroll", "hover", "wait"]
    selector: str = ""


@dataclass(frozen=True)
class ExtractionAction:
    """Reads structured data using a cached PortalDictionary schema. Zero LLM cost."""
    type: Literal["extraction"] = field(default="extraction", init=False)
    schema_id: str           # key into PortalDictionary
    target_selector: str = ""


@dataclass(frozen=True)
class TransitionAction:
    """
    One or more MotorCommands that together cause a structural DOM change.
    The sequence is atomic from the Thread's perspective — all commands must
    succeed for the transition to be recorded.
    """
    type: Literal["transition"] = field(default="transition", init=False)
    commands: tuple[MotorCommand, ...] = field(default_factory=tuple)
    expected_next_room: str | None = None  # hint for fast routing, not enforced


Action = PassiveAction | ExtractionAction | TransitionAction
