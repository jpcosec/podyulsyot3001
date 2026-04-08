"""Ariadne Error Taxonomy — Standardized Automation Exceptions.

These exceptions are motor-agnostic and allow the CLI/TUI to react
consistently to failures (e.g., triggering a manual recovery or a retry).
"""

from __future__ import annotations

from typing import Any, Optional


class AriadneError(Exception):
    """Base class for all Ariadne-related errors."""

    def __init__(
        self,
        message: str,
        step_index: Optional[int] = None,
        state_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.step_index = step_index
        self.state_id = state_id


class ObservationFailed(AriadneError):
    """The page state did not match the expected AriadneObserve predicate."""

    pass


class TargetNotFound(AriadneError):
    """A specific element (AriadneTarget) could not be resolved by the motor."""

    pass


class InteractionFailed(AriadneError):
    """The motor found the element but failed to interact (e.g., element intercepted)."""

    pass


class TerminalStateReached(AriadneError):
    """The automation reached a known failure state (e.g., 'Already Applied')."""

    pass


class TaskAborted(AriadneError):
    """The task was manually aborted or reached an unrecoverable blocker."""

    pass


class TranslationError(AriadneError):
    """The Ariadne common intent could not be translated for the current motor."""

    pass


class PortalDriftError(AriadneError):
    """The portal structure has changed significantly, breaking the map."""

    pass


class HumanInterventionRequired(AriadneError):
    """The run paused so an operator can inspect and safely resume the session."""

    def __init__(
        self,
        message: str,
        *,
        reason: str,
        step_index: Optional[int] = None,
        state_id: Optional[str] = None,
        details: Optional[dict[str, object]] = None,
    ):
        super().__init__(message, step_index=step_index, state_id=state_id)
        self.reason = reason
        self.details = details or {}


class FormReviewRequired(HumanInterventionRequired):
    """Raised when an analyzed form requires human review."""

    def __init__(
        self,
        message: str,
        *,
        form: Any,  # AnalyzedForm
        reason: str = "form_review_required",
        step_index: Optional[int] = None,
        state_id: Optional[str] = None,
        details: Optional[dict[str, object]] = None,
    ):
        super().__init__(
            message,
            reason=reason,
            step_index=step_index,
            state_id=state_id,
            details=details,
        )
        self.form = form
