"""ModeRegistry for dynamic URL-to-AriadneMode mapping."""

import importlib
import pkgutil
from typing import Dict

from src.automation.ariadne.modes.base import AriadneMode
from src.automation.ariadne.modes.default import DefaultMode
from src.automation.portals.modes.portals import JsonConfigMode


class ModeRegistry:
    """Registry to select the correct AriadneMode for a given session URL."""

    _mapping: Dict[str, AriadneMode] = {}
    _loaded = False
    _default_mode: AriadneMode | None = None

    @classmethod
    def _register_mode_instance(cls, obj):
        """Register a mode instance for its URL patterns."""
        if not (
            isinstance(obj, type)
            and issubclass(obj, AriadneMode)
            and obj is not AriadneMode
            and hasattr(obj, "url_patterns")
        ):
            return
        mode_instance = obj()
        patterns = getattr(obj, "url_patterns")
        if isinstance(patterns, list):
            for pattern in patterns:
                cls._mapping[pattern.lower()] = mode_instance

    @classmethod
    def _discover_modes(cls):
        """Perform dynamic discovery of AriadneMode implementations in portals."""
        if cls._loaded:
            return

        JsonConfigMode.preload_configs()

        try:
            import src.automation.portals.modes as portals_modes

            for _, module_name, _ in pkgutil.walk_packages(
                portals_modes.__path__, portals_modes.__name__ + "."
            ):
                try:
                    module = importlib.import_module(module_name)
                    for _, obj in vars(module).items():
                        cls._register_mode_instance(obj)
                except Exception:
                    continue
        except ImportError:
            pass

        cls._loaded = True

    @classmethod
    def get_mode_for_url(cls, url: str) -> AriadneMode:
        """Select and instantiate the mode corresponding to the provided URL."""
        if not cls._loaded:
            cls._discover_modes()

        if not url:
            return cls._get_default_mode()

        url_lower = url.lower()
        for pattern, mode_instance in cls._mapping.items():
            if pattern in url_lower:
                return mode_instance

        return cls._get_default_mode()

    @classmethod
    def _get_default_mode(cls) -> AriadneMode:
        if cls._default_mode is None:
            cls._default_mode = DefaultMode()
        return cls._default_mode
