"""Ariadne Translator Registry — Mapping Commands to Translators."""

from typing import Dict, Type

from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    CrawlCommand,
    MotorCommand,
)
from src.automation.ariadne.translators.base import AriadneTranslator
from src.automation.ariadne.translators.browseros import BrowserOSTranslator
from src.automation.ariadne.translators.crawl4ai import Crawl4AITranslator


class TranslatorRegistry:
    """Registry to resolve the correct JIT Translator for a given Command type."""

    _mapping: Dict[Type[MotorCommand], AriadneTranslator] = {
        BrowserOSCommand: BrowserOSTranslator(),
        CrawlCommand: Crawl4AITranslator(),
    }

    @classmethod
    def get_translator_for_command(cls, command_type: Type[MotorCommand]) -> AriadneTranslator:
        """Returns the translator instance for the specified command type."""
        translator = cls._mapping.get(command_type)
        if not translator:
            # Fallback or error
            return Crawl4AITranslator()
        return translator

    @classmethod
    def get_translator_by_name(cls, name: str) -> AriadneTranslator:
        """Returns a translator instance by motor name."""
        if name.lower() == "browseros":
            return BrowserOSTranslator()
        return Crawl4AITranslator()
