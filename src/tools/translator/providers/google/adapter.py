"""Google Translate adapter via deep-translator."""
from src.translator.base import BaseTranslatorAdapter, ToolDependencyError

class GoogleTranslatorAdapter(BaseTranslatorAdapter):
    """Adapter using the deep_translator GoogleTranslator."""

    @property
    def provider_name(self) -> str:
        return "google"

    def translate_chunk(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise ToolDependencyError("deep-translator is required for this adapter. Run: pip install deep-translator") from exc
        
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)
