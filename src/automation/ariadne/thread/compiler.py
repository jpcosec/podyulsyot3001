"""Thread → C4AScript compiler (Level 0 execution).

A verified AriadneThread can be compiled to a standalone C4AScript that runs
without LangGraph overhead. If execution fails, the caller degrades to Level 1.

Usage:
    script = compile(thread)
    # run via CrawlerRunConfig(c4a_script=script)
"""

from __future__ import annotations

from src.automation.ariadne.thread.thread import AriadneThread
from src.automation.ariadne.thread.action import TransitionAction, PassiveAction, ExtractionAction
from src.automation.ariadne.thread.translators import translate_command, translate_passive, translate_extraction


def compile(thread: AriadneThread) -> str:
    """Translate all transitions of a thread to a C4AScript string."""
    lines = [f"# {thread.portal_name}/{thread.mission_id}"]
    for t in thread._transitions:
        lines.append(f"# {t.room_from} → {t.room_to}")
        lines.extend(_translate_actions(t.actions))
    return "\n".join(lines)


def _translate_actions(actions) -> list[str]:
    lines = []
    for action in actions:
        lines.extend(_translate_action(action))
    return lines


def _translate_action(action) -> list[str]:
    if isinstance(action, TransitionAction):
        return [translate_command(c) for c in action.commands]
    if isinstance(action, PassiveAction):
        return [translate_passive(action)]
    if isinstance(action, ExtractionAction):
        return [translate_extraction(action)]
    return [f"# unknown action type: {type(action).__name__}"]
