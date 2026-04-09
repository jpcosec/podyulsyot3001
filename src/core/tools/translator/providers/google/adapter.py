"""Google Translate adapter via deep-translator."""

import sys

from src.core.tools.translator.base import BaseTranslatorAdapter, ToolDependencyError


def _debug(msg: str) -> None:
    print(f"[DEBUG GOOGLE] {msg}", file=sys.stderr)


class GoogleTranslatorAdapter(BaseTranslatorAdapter):
    """Adapter using the deep_translator GoogleTranslator."""

    @property
    def provider_name(self) -> str:
        """Return the canonical provider key for the Google adapter."""
        return "google"

    def translate_chunk(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate one text chunk with ``deep_translator``.

        Args:
            text: Text chunk to translate.
            source_lang: Source language code.
            target_lang: Target language code.

        Returns:
            The translated text chunk.
        """
        _debug(
            f"translate_chunk called: {source_lang} -> {target_lang}: {text[:50]}..."
        )
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise ToolDependencyError(
                "deep-translator is required for this adapter. Run: pip install deep-translator"
            ) from exc

        translator = GoogleTranslator(source=source_lang, target=target_lang)
        result = translator.translate(text)
        _debug(f"translate_chunk result: {result[:50] if result else 'None'}...")
        return result
