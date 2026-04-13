"""Repository - map loading helpers."""

import asyncio
from pathlib import Path

from src.automation.ariadne.io import read_json, read_json_async
from src.automation.ariadne.models import AriadneMap


def load_map_sync(base_dir: Path, portal_name: str, map_type: str) -> AriadneMap:
    """Load map from disk synchronously."""
    map_path = base_dir / portal_name / "maps" / f"{map_type}.json"
    try:
        return AriadneMap.model_validate(read_json(map_path))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Ariadne Map not found for '{portal_name}' (type: {map_type}) at {map_path}"
        ) from exc


async def load_map_async(base_dir: Path, portal_name: str, map_type: str) -> AriadneMap:
    """Load map from disk asynchronously."""
    map_path = base_dir / portal_name / "maps" / f"{map_type}.json"
    try:
        map_payload = await read_json_async(map_path)
        return await asyncio.to_thread(AriadneMap.model_validate, map_payload)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Ariadne Map not found for '{portal_name}' (type: {map_type}) at {map_path}"
        ) from exc


def resolve_sync_or_async() -> bool:
    """Determine if we should use sync or async loading."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return False
    return loop and loop.is_running()


def choose_loader():
    """Choose appropriate loader based on context."""
    if resolve_sync_or_async():
        return load_map_async
    return load_map_sync
