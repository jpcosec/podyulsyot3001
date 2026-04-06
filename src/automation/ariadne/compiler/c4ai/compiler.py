"""Ariadne-to-Crawl4AI Compiler.

Turns a high-level AriadnePath and Task into a C4AI-IR (Intermediate Representation)
which can then be serialized into a C4A-Script string.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from src.automation.ariadne.models import (
    AriadneAction,
    AriadneIntent,
    AriadnePath,
    AriadneStep,
    AriadneTarget,
)
from .ir import (
    C4AIIf,
    C4AIInstruction,
    C4AIInteract,
    C4AINavigate,
    C4AIScriptIR,
    C4AIWait,
)

logger = logging.getLogger(__name__)


class AriadneC4AICompiler:
    """Compiles a backend-neutral Ariadne Path into a motor-specific C4AI-IR."""

    def compile(self, path: AriadnePath) -> C4AIScriptIR:
        """Main entry point for compilation."""
        logger.info("Compiling AriadnePath '%s' to C4AI-IR", path.id)
        instructions: List[C4AIInstruction] = []

        for step in path.steps:
            instructions.extend(self._compile_step(step))

        return C4AIScriptIR(instructions=instructions)

    def _compile_step(self, step: AriadneStep) -> List[C4AIInstruction]:
        """Compiles a single AriadneStep into one or more C4AI instructions."""
        ir_steps: List[C4AIInstruction] = []

        # 1. Observation Guards (Wait for presence)
        if step.observe and step.observe.required_elements:
            for target in step.observe.required_elements:
                if target.css:
                    ir_steps.append(C4AIWait(selector=target.css))
                else:
                    logger.warning(
                        "Step '%s' has required_element with no CSS target; skipping C4AI wait.", 
                        step.name
                    )

        # 2. Actions
        for action in step.actions:
            ir_steps.extend(self._compile_action(action))

        return ir_steps

    def _compile_action(self, action: AriadneAction) -> List[C4AIInstruction]:
        """Compiles a single AriadneAction into a C4AI instruction."""
        if not action.target or not action.target.css:
            if action.intent == AriadneIntent.NAVIGATE and action.value:
                return [C4AINavigate(url=action.value)]
            
            logger.warning(
                "Action with intent '%s' has no CSS target; skipping in C4AI compilation.", 
                action.intent
            )
            return []

        selector = action.target.css
        value = action.value

        # Map Ariadne Intent to C4AI Interaction Type
        mapping = {
            AriadneIntent.CLICK: "CLICK",
            AriadneIntent.FILL: "SET",
            AriadneIntent.FILL_REACT: "SET",  # C4A-Script handles React internally in some cases
            AriadneIntent.SELECT: "SELECT",
            AriadneIntent.UPLOAD: "UPLOAD",
        }

        if action.intent in mapping:
            return [
                C4AIInteract(
                    type=mapping[action.intent], 
                    selector=selector, 
                    value=value
                )
            ]
        
        if action.intent == AriadneIntent.WAIT:
            return [C4AIWait(selector=selector)]

        logger.warning("Unsupported AriadneIntent '%s' in C4AI compiler.", action.intent)
        return []
