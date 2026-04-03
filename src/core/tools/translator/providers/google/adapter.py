"""Google Translate adapter via deep-translator."""

from src.core.tools.translator.base import BaseTranslatorAdapter, ToolDependencyError


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
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise ToolDependencyError(
                "deep-translator is required for this adapter. Run: pip install deep-translator"
            ) from exc

        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)
