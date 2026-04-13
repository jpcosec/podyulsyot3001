"""CLI runtime config helpers."""

import uuid

from src.automation.ariadne.core.actors import Theseus
from src.automation.ariadne.core.cognition import AriadneThread, Labyrinth
from src.automation.ariadne.models import AriadneMap


def build_config(
    adapter,
    motor_name: str,
    thread_id: str,
    labyrinth: Labyrinth | None = None,
    ariadne_thread: AriadneThread | None = None,
) -> dict:
    """Build a shared graph execution config."""
    return {
        "configurable": {
            "thread_id": thread_id,
            "executor": adapter,
            "motor_name": motor_name,
            "record_graph": True,
            "labyrinth": labyrinth,
            "ariadne_thread": ariadne_thread,
        }
    }


def build_theseus(
    adapter, labyrinth: Labyrinth, ariadne_thread: AriadneThread
) -> Theseus:
    """Build the mission coordinator."""
    return Theseus(adapter, adapter, labyrinth, ariadne_thread)


async def load_runtime_cognition(
    source: str, portal_mode: str, mission_id: Optional[str]
) -> tuple[Labyrinth, AriadneThread]:
    """Load runtime cognition objects for the active portal and mission."""
    labyrinth = await Labyrinth.load_from_db(source, map_type=portal_mode)
    ariadne_thread = await AriadneThread.load_from_db(
        source, mission_id=mission_id, map_type=portal_mode
    )
    return labyrinth, ariadne_thread


async def prepare_runtime_config(
    adapter, motor_name: str, source: str, portal_mode: str, mission_id: Optional[str]
) -> tuple[str, dict, Theseus]:
    """Build runtime config and the mission coordinator."""
    labyrinth, ariadne_thread = await load_runtime_cognition(
        source, portal_mode, mission_id
    )
    thread_id = str(uuid.uuid4())
    config = build_config(adapter, motor_name, thread_id, labyrinth, ariadne_thread)
    return thread_id, config, build_theseus(adapter, labyrinth, ariadne_thread)
