"""Skeleton — abstract structural representation of a page.

The skeleton is invariant to slot content (text, values).
It only changes when elements are added, removed, or reclassified.
That structural change is what defines a Transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ElementType(StrEnum):
    navbar      = "navbar"
    modal       = "modal"
    form        = "form"
    text_field  = "text_field"
    button      = "button"
    list        = "list"
    card        = "card"
    text        = "text"
    link        = "link"
    image       = "image"
    dropdown    = "dropdown"
    control     = "control"   # generic interactive element (accordion, toggle, etc.)
    unknown     = "unknown"


@dataclass(frozen=True)
class AbstractElement:
    """One typed node in the skeleton tree."""

    type: ElementType
    role: str             # semantic label, e.g. "submit_button", "search_field"
    selector: str         # stable CSS selector used by Motor and PortalDictionary
    slots: tuple[str, ...] = field(default_factory=tuple)  # variable content holes


@dataclass(frozen=True)
class Skeleton:
    """
    Structural fingerprint of a page.

    Two skeletons are equal if they have the same set of (type, role) pairs,
    regardless of selector stability or slot values. Selector changes don't
    constitute a structural change — they're a PortalDictionary concern.
    """

    elements: tuple[AbstractElement, ...] = field(default_factory=tuple)

    def is_transition_from(self, other: "Skeleton") -> bool:
        """True if this skeleton differs structurally from other (new, removed, or reclassified elements)."""
        def fingerprint(s: "Skeleton") -> frozenset[tuple[str, str]]:
            return frozenset((e.type, e.role) for e in s.elements)
        return fingerprint(self) != fingerprint(other)

    def to_dict(self) -> dict:
        return {
            "elements": [
                {"type": e.type, "role": e.role, "selector": e.selector, "slots": list(e.slots)}
                for e in self.elements
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Skeleton":
        elements = tuple(
            AbstractElement(
                type=ElementType(e["type"]),
                role=e["role"],
                selector=e["selector"],
                slots=tuple(e.get("slots", [])),
            )
            for e in data.get("elements", [])
        )
        return cls(elements=elements)
