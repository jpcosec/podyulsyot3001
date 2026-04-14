"""C4AScript translators — one function per action/command type.

Each function maps a domain object to one or more C4AScript instruction strings.
"""

from __future__ import annotations

from src.automation.contracts.motor import MotorCommand
from src.automation.ariadne.thread.action import PassiveAction, ExtractionAction


def translate_command(command: MotorCommand) -> str:
    match command.operation:
        case "click" | "submit":
            return f"CLICK `{command.selector}`"
        case "fill":
            return f'SET `{command.selector}` "{command.value or ""}"'
        case "navigate":
            return f"GO {command.value}"
        case "scroll":
            return f"SCROLL DOWN {command.value or 500}"
        case "wait":
            return f"WAIT {command.wait_for or 1}"
        case _:
            return f"# unsupported operation: {command.operation}"


def translate_passive(action: PassiveAction) -> str:
    match action.operation:
        case "scroll":
            return "SCROLL DOWN 500"
        case "wait":
            return "WAIT 1"
        case "hover":
            sel = action.selector.replace("'", "\\'")
            return f"EVAL `document.querySelector('{sel}').dispatchEvent(new Event('mouseover'))`"
        case _:
            return f"# unsupported passive: {action.operation}"


def translate_extraction(action: ExtractionAction) -> str:
    return f"# ExtractionAction({action.schema_id}) — runs via PortalExtractor, not C4AScript"
