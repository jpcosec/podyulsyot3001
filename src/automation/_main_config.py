"""CLI profile and config helpers."""

import os
import json
from typing import Optional

from src.automation.contracts import CandidateProfile
from src.automation.ariadne.models import AriadneMap
from src.automation.ariadne.core.cognition.labyrinth import Labyrinth
from src.automation.ariadne.exceptions import MapNotFoundError
from src.automation.motors.registry import MotorRegistry


class CliInputError(ValueError):
    """Raised when CLI inputs are invalid before execution starts."""


class CliExecutionError(RuntimeError):
    """Raised when a CLI flow cannot be started or completed."""


def default_profile() -> CandidateProfile:
... (rest of the file ...)

async def load_map(source: str, portal_mode: str) -> AriadneMap:
    """Load and validate the requested Ariadne map."""
    try:
        lab = await Labyrinth.load_from_db(source, map_type=portal_mode)
        return lab.ariadne_map
    except MapNotFoundError as exc:
        raise CliExecutionError(str(exc)) from exc
    except ValueError as exc:
        raise CliExecutionError(f"Failed to validate map: {exc}") from exc

    except ValueError as exc:
        raise CliExecutionError(f"Failed to validate map: {exc}") from exc


def adapter_kwargs(motor_name: str) -> dict:
    """Build backend-specific adapter kwargs from the environment."""
    if motor_name != "browseros":
        return {}
    return {
        "base_url": os.environ.get("BROWSEROS_BASE_URL", "http://127.0.0.1:9000"),
        "appimage_path": os.environ.get("BROWSEROS_APPIMAGE_PATH"),
    }


def get_adapter(motor_name: str):
    """Resolve a browser adapter instance from the motor registry."""
    try:
        return MotorRegistry.get_adapter(motor_name, **adapter_kwargs(motor_name))
    except ValueError as exc:
        raise CliInputError(str(exc)) from exc
