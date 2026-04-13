"""Crawl4AI Ariadne translator."""

from __future__ import annotations

from typing import Optional

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    CrawlCommand,
    MotorCommand,
)
from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.translators.base import AriadneTranslator
from src.automation.adapters.translators._crawl4ai_builders import build_c4a_script


class Crawl4AITranslator(AriadneTranslator):
    """Translate Ariadne intents into native C4A-Script."""

    command_types = (CrawlCommand,)
    motor_names = ("crawl4ai",)

    def _resolve_selector(self, target: AriadneTarget, intent: AriadneIntent) -> str:
        """Resolve selector from target based on available attributes."""
        if target.css:
            return target.css
        if target.text:
            return f"text={target.text}"
        if target.hint:
            return f"[data-ariadne-hint='{target.hint}']"
        if intent != AriadneIntent.PRESS:
            raise ValueError(f"Target {target} has no css, text, or hint selector.")
        return ""

    def translate_intent(
        self,
        intent: AriadneIntent,
        target: AriadneTarget,
        state: AriadneState,
        value: Optional[str] = None,
    ) -> MotorCommand:
        selector = self._resolve_selector(target, intent)
        resolved_value = self.resolve_placeholders(value, state) if value else ""
        script = build_c4a_script(intent, selector, resolved_value)
        return CrawlCommand(c4a_script=script, hooks=[])

    def translate_batch(
        self,
        batch: list[tuple[AriadneIntent, AriadneTarget, Optional[str]]],
        state: AriadneState,
    ) -> MotorCommand:
        lines = []
        combined_hooks: list[dict[str, object]] = []

        for index, (intent, target, value) in enumerate(batch):
            command = self.translate_intent(intent, target, state, value)
            if not isinstance(command, CrawlCommand):
                continue
            lines.append(f"# Action {index}")
            lines.append(command.c4a_script)

        return CrawlCommand(c4a_script="\n".join(lines), hooks=combined_hooks)
