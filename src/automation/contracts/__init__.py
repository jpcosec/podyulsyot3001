"""contracts — shared protocols and data types. Imported by all layers."""

from src.automation.contracts.sensor import Sensor, SnapshotResult
from src.automation.contracts.motor import Motor, MotorCommand, TraceEvent, ExecutionResult
from src.automation.contracts.state import AriadneState
from src.automation.contracts.llm import LLMClient
from src.automation.contracts.extractor import Extractor

__all__ = [
    "Sensor", "SnapshotResult",
    "Motor", "MotorCommand", "TraceEvent", "ExecutionResult",
    "AriadneState",
    "LLMClient",
    "Extractor",
]
