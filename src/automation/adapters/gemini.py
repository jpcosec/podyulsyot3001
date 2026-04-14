"""GeminiClient — LLMClient backed by Google Gemini (google-genai SDK)."""

from __future__ import annotations

import base64

from google import genai
from google.genai import types


class GeminiClient:
    """Async wrapper around the google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, prompt: str, image_b64: str | None = None) -> str:
        contents = _build_contents(prompt, image_b64)
        response = await self._client.aio.models.generate_content(
            model=self._model, contents=contents
        )
        return response.text


def _build_contents(prompt: str, image_b64: str | None) -> list:
    if not image_b64:
        return [prompt]
    image_bytes = base64.b64decode(image_b64)
    return [types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), prompt]
