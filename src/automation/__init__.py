"""Unified Automation Package.

This package provides a backend-neutral system for browser automation,
utilizing the Ariadne semantic layer to decouple portal logic from
execution engines.
"""

from .storage import AutomationStorage
from .contracts import ApplyJobContext, CandidateProfile, ExecutionContext

__all__ = [
    "ApplyJobContext",
    "CandidateProfile",
    "ExecutionContext",
    "AutomationStorage",
]
