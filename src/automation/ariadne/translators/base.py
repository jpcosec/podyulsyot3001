import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    MotorCommand,
)
from src.automation.ariadne.models import (
    AriadneState,
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

    def _lookup_placeholder(self, key: str, state: AriadneState) -> str | None:
        """Look up a placeholder key in state sources."""
        for source in ("profile_data", "job_data", "session_memory"):
            data = state.get(source, {})
            if key in data:
                return str(data[key])
        return None

    def resolve_placeholders(self, text: str, state: AriadneState) -> str:
        """Resolves {{placeholder}} patterns in text using AriadneState."""
        if not text:
            return text

        def replace_match(match):
            key = match.group(1).strip()
            value = self._lookup_placeholder(key, state)
            return value if value is not None else match.group(0)

        return re.sub(r"\{\{(.*?)\}\}", replace_match, text)
