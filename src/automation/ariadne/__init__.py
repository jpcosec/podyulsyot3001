"""Ariadne — The Semantic Path Knowledge Subsystem."""

from .exceptions import (
    AriadneError,
    InteractionFailed,
    ObservationFailed,
    PortalDriftError,
    TargetNotFound,
    TaskAborted,
    TerminalStateReached,
    TranslationError,
)
from .models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadnePath,
    AriadnePortalMap,
    AriadneState,
    AriadneStep,
    AriadneTarget,
    AriadneTask,
)
from .motor_protocol import MotorProvider, MotorSession
from .navigator import AriadneNavigator
from .recorder import AriadneRecorder
from .trace_models import AriadneSessionTrace, RawTraceEvent

__all__ = [
    # Models
    "AriadneTarget",
    "AriadneIntent",
    "AriadneAction",
    "AriadneObserve",
    "AriadneState",
    "AriadneTask",
    "AriadneStep",
    "AriadnePath",
    "AriadnePortalMap",
    # Logic
    "AriadneNavigator",
    "AriadneRecorder",
    # Motor Protocol
    "MotorProvider",
    "MotorSession",
    # Traces
    "AriadneSessionTrace",
    "RawTraceEvent",
    # Exceptions
    "AriadneError",
    "ObservationFailed",
    "TargetNotFound",
    "InteractionFailed",
    "TerminalStateReached",
    "TaskAborted",
    "TranslationError",
    "PortalDriftError",
]
