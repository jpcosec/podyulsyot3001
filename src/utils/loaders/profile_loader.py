from pathlib import Path
from typing import Any

from src.utils.loader import load_json


def load_base_profile(profile_path: Path) -> dict[str, Any]:
    return load_json(profile_path)
