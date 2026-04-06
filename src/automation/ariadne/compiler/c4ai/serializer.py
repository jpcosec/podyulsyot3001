"""C4AI-IR to C4A-Script Serializer.

Turns C4AI-IR instructions into a raw C4A-Script string suitable for execution
via AsyncWebCrawler.arun(js_code="...").
"""

from __future__ import annotations

from typing import List
from .ir import (
    C4AIIf,
    C4AIInstruction,
    C4AIInteract,
    C4AINavigate,
    C4AIScriptIR,
    C4AIWait,
)


class C4AIScriptSerializer:
    """Serializes C4AI-IR into the final C4A-Script DSL."""

    def serialize(self, ir: C4AIScriptIR) -> str:
        """Main entry point for serialization."""
        return "\n".join(self._serialize_instructions(ir.instructions))

    def _serialize_instructions(self, instructions: List[C4AIInstruction]) -> List[str]:
        """Recursive helper for serializing lists of instructions."""
        lines = []
        for instr in instructions:
            lines.extend(self._serialize_single(instr))
        return lines

    def _serialize_single(self, instr: C4AIInstruction) -> List[str]:
        """Serializes one instruction into one or more lines of C4A-Script."""
        if isinstance(instr, C4AINavigate):
            return [f"NAVIGATE {instr.url}"]
            
        if isinstance(instr, C4AIWait):
            return [f"WAIT {instr.selector} {instr.timeout}"]
            
        if isinstance(instr, C4AIInteract):
            value_part = f" \"{instr.value}\"" if instr.value else ""
            return [f"{instr.type} {instr.selector}{value_part}"]
            
        if isinstance(instr, C4AIIf):
            lines = [f"IF {instr.condition_selector}"]
            # Indent the true branch
            true_lines = self._serialize_instructions(instr.true_branch)
            lines.extend([f"  {line}" for line in true_lines])
            
            if instr.false_branch:
                lines.append("ELSE")
                # Indent the false branch
                false_lines = self._serialize_instructions(instr.false_branch)
                lines.extend([f"  {line}" for line in false_lines])
            
            lines.append("END")
            return lines

        return []
