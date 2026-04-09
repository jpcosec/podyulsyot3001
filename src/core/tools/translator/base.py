"""Base framework for translation logic.

Implements chunking, retries, and explicit errors.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, List, Optional
import os
import json
import logging

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class ToolDependencyError(Exception):
    """Raised when a required translation dependency is unavailable."""


class ToolFailureError(Exception):
    """Raised when translation retries are exhausted."""


class BaseTranslatorAdapter(ABC):
    """Abstract base class for all translation engines."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the translation provider (e.g. 'google', 'deepl')."""
        pass

    @property
    def max_chunk_chars(self) -> int:
        """Maximum characters allowed in a translated chunk."""
        return 4500

    @property
    def max_attempts(self) -> int:
        """Maximum attempts allowed for translating one chunk."""
        return 2

    @property
    def retry_delay_seconds(self) -> float:
        """Delay between chunk translation retries in seconds."""
        return 1.0

    @abstractmethod
    def translate_chunk(self, text: str, source_lang: str, target_lang: str) -> str:
        """Provider-specific translation for a single text chunk."""
        pass

    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.max_chunk_chars:
            return [text]

        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for line in text.splitlines():
            line_len = len(line) + 1
            if line_len > self.max_chunk_chars:
                if current:
                    chunks.append("\n".join(current))
                    current = []
                    current_len = 0
                start = 0
                while start < len(line):
                    end = min(start + self.max_chunk_chars, len(line))
                    chunks.append(line[start:end])
                    start = end
                continue

            if current_len + line_len > self.max_chunk_chars and current:
                chunks.append("\n".join(current))
                current = [line]
                current_len = line_len
            else:
                current.append(line)
                current_len += line_len

        if current:
            chunks.append("\n".join(current))

        return chunks

    def translate_text(
        self, text: str, target_lang: str = "en", source_lang: str = "auto"
    ) -> str:
        """Translate full text with bounded retries and automatic chunking."""
        if not text or not text.strip():
            return text

        if source_lang == target_lang:
            return text

        last_error: Optional[Exception] = None
        chunks = self._chunk_text(text)
        translated_chunks: List[str] = []

        for chunk in chunks:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    translated = self.translate_chunk(chunk, source_lang, target_lang)
                    translated_chunks.append(str(translated))
                    break
                except Exception as exc:
                    last_error = exc
                    import traceback

                    tb = traceback.format_exc()
                    logger.warning(
                        f"{LogTag.WARN} [{self.provider_name}] Chunk translation failed on attempt {attempt}/{self.max_attempts}: {exc}\nTraceback: {tb}"
                    )
                    if attempt < self.max_attempts and self.retry_delay_seconds > 0:
                        time.sleep(self.retry_delay_seconds)
            else:
                # All attempts failed for this chunk
                logger.error(
                    f"{LogTag.FAIL} [{self.provider_name}] All {self.max_attempts} translation attempts failed for chunk: {chunk[:100]}..."
                )

        if translated_chunks and len(translated_chunks) == len(chunks):
            return "\n".join(translated_chunks)

        raise ToolFailureError(
            f"Translation failed after {self.max_attempts} attempts."
        ) from last_error

    def translate_fields(
        self,
        payload: dict[str, Any],
        fields: List[str],
        target_lang: str = "en",
        source_lang: str = "auto",
    ) -> dict[str, Any]:
        """Translate selected top-level string fields in a JSON/dict payload."""
        out = dict(payload)
        for field in fields:
            value = out.get(field)
            if isinstance(value, str) and value:
                out[field] = self.translate_text(
                    value, target_lang=target_lang, source_lang=source_lang
                )
            elif isinstance(value, list) and all(isinstance(i, str) for i in value):
                # Handle lists of strings (e.g. responsibilities, requirements)
                out[field] = [
                    self.translate_text(
                        item, target_lang=target_lang, source_lang=source_lang
                    )
                    for item in value
                ]
        return out
