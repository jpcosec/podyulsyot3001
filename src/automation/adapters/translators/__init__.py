"""Motor-specific Ariadne translators."""

from src.automation.adapters.translators.browseros import BrowserOSTranslator
from src.automation.adapters.translators.crawl4ai import Crawl4AITranslator
from src.automation.adapters.translators.registry import TranslatorRegistry

__all__ = [
    "BrowserOSTranslator",
    "Crawl4AITranslator",
    "TranslatorRegistry",
]
