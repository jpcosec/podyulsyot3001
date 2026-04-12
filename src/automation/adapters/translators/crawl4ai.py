"""Crawl4AI Ariadne translator."""

from __future__ import annotations

import json
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
    """Translate Ariadne intents into Crawl4AI scripts."""

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
        safe_selector = json.dumps(selector)
        safe_value = json.dumps(resolved_value)
        hooks: list[dict[str, object]] = []

        if intent == AriadneIntent.CLICK:
            script = f"await page.click({safe_selector})"
        elif intent == AriadneIntent.FILL:
            script = f"await page.fill({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.SELECT:
            script = f"await page.select_option({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.PRESS:
            script = f"await page.press({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.UPLOAD:
            script = f"await page.set_input_files({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.WAIT:
            if resolved_value.isdigit():
                script = f"await page.wait_for_timeout({resolved_value})"
            else:
                script = f"await page.wait_for_selector({safe_selector})"
        elif intent == AriadneIntent.EXTRACT:
            script = f"await page.inner_text({safe_selector})"
        else:
            raise ValueError(f"Unsupported intent for Crawl4AI: {intent}")

        return CrawlCommand(c4a_script=script, hooks=hooks)

    def translate_batch(
        self,
        batch: list[tuple[AriadneIntent, AriadneTarget, Optional[str]]],
        state: AriadneState,
    ) -> MotorCommand:
        final_js_script = ["try {"]
        combined_hooks: list[dict[str, object]] = []

        for index, (intent, target, value) in enumerate(batch):
            command = self.translate_intent(intent, target, state, value)
            if not isinstance(command, CrawlCommand):
                continue

            final_js_script.append(f"  // Action {index}")
            final_js_script.append("  try {")
            final_js_script.append(f"    {command.c4a_script};")
            final_js_script.append("  } catch (e) {")
            final_js_script.append(
                f"    return {{ 'failed_at': {index}, 'completed_count': {index}, 'error': e.message }};"
            )
            final_js_script.append("  }")
            combined_hooks.extend(command.hooks)

        final_js_script.append(f"  return {{ 'completed_count': {len(batch)} }};")
        final_js_script.append("} catch (e) {")
        final_js_script.append(
            "  return { 'failed_at': -1, 'completed_count': 0, 'error': `Unexpected batch error: ${e.message}` };"
        )
        final_js_script.append("}")

        return CrawlCommand(c4a_script="\n".join(final_js_script), hooks=combined_hooks)
