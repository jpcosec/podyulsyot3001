"""BrowserOS Ariadne translator."""

from __future__ import annotations

from typing import Optional

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    BrowserOSCommand,
    MotorCommand,
)
from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.translators.base import AriadneTranslator


class BrowserOSTranslator(AriadneTranslator):
    """Translate Ariadne intents into BrowserOS commands."""

    command_types = (BrowserOSCommand,)
    motor_names = ("browseros",)

    def translate_intent(
        self,
        intent: AriadneIntent,
        target: AriadneTarget,
        state: AriadneState,
        value: Optional[str] = None,
    ) -> MotorCommand:
        selector_text = target.text or target.hint or target.css
        if not selector_text:
            raise ValueError(f"Target {target} has no text, hint, or css selector.")

        resolved_value = self.resolve_placeholders(value, state) if value else None

        if intent == AriadneIntent.CLICK:
            return BrowserOSCommand(
                tool="click", selector_text=selector_text, value=resolved_value
            )
        if intent == AriadneIntent.FILL:
            return BrowserOSCommand(
                tool="fill", selector_text=selector_text, value=resolved_value
            )
        if intent == AriadneIntent.UPLOAD:
            return BrowserOSCommand(
                tool="upload", selector_text=selector_text, value=resolved_value
            )
        if intent == AriadneIntent.PRESS:
            return BrowserOSCommand(
                tool="press", selector_text=selector_text, value=resolved_value
            )
        if intent == AriadneIntent.SELECT:
            return BrowserOSCommand(
                tool="click", selector_text=selector_text, value=resolved_value
            )

        raise ValueError(f"Unsupported intent for BrowserOS: {intent}")

    def translate_batch(
        self,
        batch: list[tuple[AriadneIntent, AriadneTarget, Optional[str]]],
        state: AriadneState,
    ) -> MotorCommand:
        if not batch:
            raise ValueError("No intents provided for translation.")

        intent, target, value = batch[0]
        return self.translate_intent(intent, target, state, value)
