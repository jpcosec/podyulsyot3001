import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.automation.ariadne.models import (
    AriadneIntent,
    AriadneState,
    AriadneTarget,
    MotorCommand,
)


class AriadneTranslator(ABC):
    """Abstract Base Class for JIT Intent Translators."""

    @abstractmethod
    def translate_intent(
        self,
        intent: AriadneIntent,
        target: AriadneTarget,
        state: AriadneState,
        value: Optional[str] = None,
    ) -> MotorCommand:
        """Translates a semantic intent into a motor-specific command."""
        pass

    @abstractmethod
    def translate_batch(
        self,
        batch: List[tuple[AriadneIntent, AriadneTarget, Optional[str]]],
        state: AriadneState,
    ) -> MotorCommand:
        """Translates a batch of semantic intents into a single motor-specific command."""
        pass

    def resolve_placeholders(self, text: str, state: AriadneState) -> str:
        """
        Resolves {{placeholder}} patterns in text using AriadneState.

        Checks state in order:
        1. profile_data
        2. job_data
        3. session_memory
        """
        if not text:
            return text

        def replace_match(match):
            key = match.group(1).strip()

            # 1. Check profile_data
            profile_data = state.get("profile_data", {})
            if key in profile_data:
                return str(profile_data[key])

            # 2. Check job_data
            job_data = state.get("job_data", {})
            if key in job_data:
                return str(job_data[key])

            # 3. Check session_memory
            session_memory = state.get("session_memory", {})
            if key in session_memory:
                return str(session_memory[key])

            # Fallback: return the original placeholder if not found
            return match.group(0)

        return re.sub(r"\{\{(.*?)\}\}", replace_match, text)
