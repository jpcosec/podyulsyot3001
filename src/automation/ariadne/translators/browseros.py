from typing import Optional

from src.automation.ariadne.models import (
    AriadneIntent,
    AriadneState,
    AriadneTarget,
    BrowserOSCommand,
    MotorCommand,
)
from src.automation.ariadne.translators.base import AriadneTranslator


class BrowserOSTranslator(AriadneTranslator):
    """
    JIT Translator for BrowserOS.
    Produces BrowserOSCommand (MCP tool calls).
    """

    def translate_intent(
        self,
        intent: AriadneIntent,
        target: AriadneTarget,
        state: AriadneState,
        value: Optional[str] = None,
    ) -> MotorCommand:
        """
        Translates AriadneIntent to BrowserOSCommand.
        """
        # 1. Resolve selector_text (BrowserOS prefers text > hint > css)
        selector_text = target.text or target.hint or target.css
        if not selector_text:
            raise ValueError(f"Target {target} has no text, hint, or css selector.")

        # 2. Resolve value placeholders
        resolved_value = self.resolve_placeholders(value, state) if value else None

        # 3. Map Intent to BrowserOS tool
        if intent == AriadneIntent.CLICK:
            return BrowserOSCommand(
                tool="click", selector_text=selector_text, value=resolved_value
            )
        elif intent == AriadneIntent.FILL:
            return BrowserOSCommand(
                tool="fill", selector_text=selector_text, value=resolved_value
            )
        elif intent == AriadneIntent.UPLOAD:
            return BrowserOSCommand(
                tool="upload", selector_text=selector_text, value=resolved_value
            )
        elif intent == AriadneIntent.PRESS:
            # For press, value is usually the key (e.g. "Enter")
            return BrowserOSCommand(
                tool="press", selector_text=selector_text, value=resolved_value
            )
        elif intent == AriadneIntent.SELECT:
            # BrowserOS often handles select by clicking the text of the option
            # or clicking the dropdown then clicking the option.
            # JIT atomic translation usually means one step.
            # If value is provided, we might be selecting by text.
            return BrowserOSCommand(
                tool="click", selector_text=selector_text, value=resolved_value
            )
        else:
            raise ValueError(f"Unsupported intent for BrowserOS: {intent}")
