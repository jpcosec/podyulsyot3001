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


class Crawl4AITranslator(AriadneTranslator):
    """Translate Ariadne intents into native C4A-Script."""

    command_types = (CrawlCommand,)
    motor_names = ("crawl4ai",)

    def translate_intent(
        self,
        intent: AriadneIntent,
        target: AriadneTarget,
        state: AriadneState,
        value: Optional[str] = None,
    ) -> MotorCommand:
        selector = target.css
        if not selector:
            if target.text:
                selector = f"text={target.text}"
            elif target.hint:
                selector = f"[data-ariadne-hint='{target.hint}']"

        if not selector:
            raise ValueError(f"Target {target} has no css, text, or hint selector.")

        resolved_value = self.resolve_placeholders(value, state) if value else ""
        script = self._build_c4a_script(intent, selector, resolved_value)
        return CrawlCommand(c4a_script=script, hooks=[])

    def _build_c4a_script(
        self, intent: AriadneIntent, selector: str, value: str
    ) -> str:
        """Build native C4A-Script command for the given intent."""
        if intent == AriadneIntent.CLICK:
            return f"CLICK `{selector}`"
        elif intent == AriadneIntent.FILL:
            escaped_value = value.replace('"', '\\"')
            return f'SET `{selector}` "{escaped_value}"'
        elif intent == AriadneIntent.SELECT:
            escaped_value = value.replace('"', '\\"')
            return f'SET `{selector}` "{escaped_value}"'
        elif intent == AriadneIntent.PRESS:
            return f"PRESS {value}"
        elif intent == AriadneIntent.UPLOAD:
            escaped_value = value.replace('"', '\\"')
            return f'SET `{selector}` "{escaped_value}"'
        elif intent == AriadneIntent.WAIT:
            if value.isdigit():
                seconds = int(value) / 1000
                return f"WAIT {seconds}"
            else:
                timeout = int(value) if value.isdigit() else 5
                return f"WAIT `{selector}` {timeout}"
        elif intent == AriadneIntent.EXTRACT:
            return f"EVAL `await page.innerText(`{selector}`)`"
        else:
            raise ValueError(f"Unsupported intent for Crawl4AI: {intent}")

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
