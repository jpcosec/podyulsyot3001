"""Unified Automation Package.

This package provides a backend-neutral system for browser automation, 
utilizing the Ariadne semantic layer to decouple portal logic from 
execution engines.
"""

from .storage import AutomationStorage

__all__ = [
    "AutomationStorage",
]
