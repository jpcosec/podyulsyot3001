"""ModeRegistry for URL-to-AriadneMode mapping."""

from typing import Type

from src.automation.ariadne.modes.base import AriadneMode
from src.automation.ariadne.modes.default import DefaultMode
from src.automation.ariadne.modes.portals import LinkedInMode, StepStoneMode, XingMode


class ModeRegistry:
    """Registry to select the correct AriadneMode for a given session URL."""

    _mapping = {
        "linkedin.com": LinkedInMode,
        "stepstone": StepStoneMode,
        "xing.com": XingMode,
    }

    @classmethod
    def get_mode_for_url(cls, url: str) -> AriadneMode:
        """Select and instantiate the mode corresponding to the provided URL."""
        if not url:
            return DefaultMode()

        for pattern, mode_class in cls._mapping.items():
            if pattern in url.lower():
                return mode_class()

        return DefaultMode()
