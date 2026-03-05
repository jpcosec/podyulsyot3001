"""Error types for non-LLM tool services."""

from __future__ import annotations


class ToolDependencyError(RuntimeError):
    """Raised when an optional runtime dependency is missing."""


class ToolFailureError(RuntimeError):
    """Raised when a tool fails after bounded retry attempts."""
