"""LLMClient — protocol for multimodal text completion."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    async def complete(self, prompt: str, image_b64: str | None = None) -> str:
        """Send a prompt (with optional screenshot) and return the model's text response."""
        ...
