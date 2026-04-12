import json
from typing import List, Optional

from src.automation.ariadne.models import (
    AriadneIntent,
    AriadneState,
    AriadneTarget,
    CrawlCommand,
    MotorCommand,
)
from src.automation.ariadne.translators.base import AriadneTranslator


class Crawl4AITranslator(AriadneTranslator):
    """
    JIT Translator for Crawl4AI.
    Produces CrawlCommand (Playwright-style script fragments).
    """

    def translate_intent(
        self,
        intent: AriadneIntent,
        target: AriadneTarget,
        state: AriadneState,
        value: Optional[str] = None,
    ) -> MotorCommand:
        """
        Translates AriadneIntent to CrawlCommand script.
        """
        # 1. Resolve selector (Prefer CSS for Crawl4AI/Playwright)
        selector = target.css
        if not selector:
            if target.text:
                # Playwright text selector
                selector = f"text={target.text}"
            elif target.hint:
                selector = f"[data-ariadne-hint='{target.hint}']"

        if not selector:
            raise ValueError(f"Target {target} has no css, text, or hint selector.")

        # 2. Resolve value placeholders
        resolved_value = self.resolve_placeholders(value, state) if value else ""

        # 3. Escape strings for use in JS/Python script fragment
        # Using json.dumps to ensure proper escaping of quotes/newlines
        safe_selector = json.dumps(selector)
        safe_value = json.dumps(resolved_value)

        # 4. Map Intent to Script Fragment
        script = ""
        hooks = []

        if intent == AriadneIntent.CLICK:
            script = f"await page.click({safe_selector})"
        elif intent == AriadneIntent.FILL:
            script = f"await page.fill({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.SELECT:
            script = f"await page.select_option({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.PRESS:
            # For press, resolved_value is the key name
            script = f"await page.press({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.UPLOAD:
            # Upload usually requires a file chooser or set_input_files
            # We can use a hook for this or a multi-line script if we know it's an input
            script = f"await page.set_input_files({safe_selector}, {safe_value})"
        elif intent == AriadneIntent.WAIT:
            # If value is numeric, wait for milliseconds, otherwise wait for selector
            if resolved_value.isdigit():
                script = f"await page.wait_for_timeout({resolved_value})"
            else:
                script = f"await page.wait_for_selector({safe_selector})"
        elif intent == AriadneIntent.EXTRACT:
            # Extraction is usually handled by the executor, but if we need a script:
            script = f"await page.inner_text({safe_selector})"
        else:
            raise ValueError(f"Unsupported intent for Crawl4AI: {intent}")

        return CrawlCommand(c4a_script=script, hooks=hooks)

    def translate_batch(
        self,
        batch: List[tuple[AriadneIntent, AriadneTarget, Optional[str]]],
        state: AriadneState,
    ) -> MotorCommand:
        """
        Translates a batch of intents into a single CrawlCommand.
        """
        scripts = []
        combined_hooks = []

        for intent, target, value in batch:
            cmd = self.translate_intent(intent, target, state, value)
            if isinstance(cmd, CrawlCommand):
                scripts.append(cmd.c4a_script)
                combined_hooks.extend(cmd.hooks)

        return CrawlCommand(c4a_script="\n".join(scripts), hooks=combined_hooks)
