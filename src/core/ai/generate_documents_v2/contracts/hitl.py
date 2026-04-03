from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

PatchAction = Literal[
    "approve",
    "reject",
    "modify",
    "request_regeneration",
    "move_to_doc",
]


class GraphPatch(BaseModel):
    action: PatchAction
    target_id: str
    new_value: Any | None = None
    feedback_note: str = ""
    persist_to_profile: bool = False
    target_stage: str | None = None
    target_type: str | None = None
