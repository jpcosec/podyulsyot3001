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
from .contracts import (
    ReplayAction,
    ReplayObserve,
    ReplayPath,
    ReplayStep,
    ReplayTarget,
    adapt_replay_path,
    adapt_replay_step,
)
from .danger_contracts import (
    ApplyDangerFinding,
    ApplyDangerReport,
    ApplyDangerSignals,
)
from .danger_detection import ApplyDangerDetector
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
    # Replay contracts
    "ReplayTarget",
    "ReplayAction",
    "ReplayObserve",
    "ReplayStep",
    "ReplayPath",
    "adapt_replay_step",
    "adapt_replay_path",
    # Danger detection
    "ApplyDangerSignals",
    "ApplyDangerFinding",
    "ApplyDangerReport",
    "ApplyDangerDetector",
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
