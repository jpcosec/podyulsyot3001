"""Crawl4AI Intermediate Representation (C4AI-IR).

Lower-level instructions that map closer to C4A-Script procedural DSL,
serving as the compiler target for Ariadne Steps.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


class C4AIInstruction(BaseModel):
    """Base unit for the IR compiler."""
    pass


class C4AINavigate(C4AIInstruction):
    url: str


class C4AIWait(C4AIInstruction):
    selector: str
    timeout: int = 15


class C4AIInteract(C4AIInstruction):
    type: Literal["CLICK", "SET", "SELECT", "UPLOAD"]
    selector: str
    value: Optional[str] = None


class C4AIIf(C4AIInstruction):
    condition_selector: str
    true_branch: List[C4AIInstruction]
    false_branch: List[C4AIInstruction] = []


class C4AIScriptIR(BaseModel):
    """The full compiled IR ready for DSL generation."""
    instructions: List[C4AIInstruction]
