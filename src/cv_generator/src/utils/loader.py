"""Load CV data from JSON files."""

import json
from pathlib import Path
from typing import Any


def load_json(file_path: str | Path) -> dict[str, Any]:
    """Load JSON file and return as dictionary.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary with JSON data
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_data(*json_files: str | Path) -> dict[str, Any]:
    """Merge multiple JSON files. Later files override earlier ones.

    Args:
        *json_files: Paths to JSON files to merge

    Returns:
        Merged dictionary
    """
    merged = {}

    for file_path in json_files:
        data = load_json(file_path)
        merged.update(data)

    return merged
