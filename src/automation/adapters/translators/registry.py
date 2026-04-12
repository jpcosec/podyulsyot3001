"""Translator discovery and lookup for motor adapters."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

from src.automation.ariadne.contracts.base import CrawlCommand, MotorCommand
from src.automation.ariadne.translators.base import AriadneTranslator


class TranslatorRegistry:
    """Resolve motor-specific translators without coupling Ariadne core to them."""

    _by_command: Dict[Type[MotorCommand], AriadneTranslator] = {}
    _by_name: Dict[str, AriadneTranslator] = {}
    _loaded = False

    @classmethod
    def _discover_translators(cls) -> None:
        if cls._loaded:
            return

        import src.automation.adapters.translators as translator_package

        for _, module_name, _ in pkgutil.walk_packages(
            translator_package.__path__, translator_package.__name__ + "."
        ):
            module = importlib.import_module(module_name)
            for obj in vars(module).values():
                if not isinstance(obj, type):
                    continue
                if not issubclass(obj, AriadneTranslator) or obj is AriadneTranslator:
                    continue

                translator = obj()
                for command_type in getattr(obj, "command_types", ()):
                    cls._by_command[command_type] = translator
                for motor_name in getattr(obj, "motor_names", ()):
                    cls._by_name[motor_name.lower()] = translator

        cls._loaded = True

    @classmethod
    def get_translator_for_command(
        cls, command_type: Type[MotorCommand]
    ) -> AriadneTranslator:
        cls._discover_translators()
        translator = cls._by_command.get(command_type)
        if translator:
            return translator
        return cls.get_translator_for_command(CrawlCommand)

    @classmethod
    def get_translator_by_name(cls, name: str) -> AriadneTranslator:
        cls._discover_translators()
        translator = cls._by_name.get(name.lower())
        if translator:
            return translator
        return cls.get_translator_for_command(CrawlCommand)
