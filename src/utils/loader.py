import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON data from a file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def merge_data(*dicts: dict) -> dict:
    """Merge multiple dictionaries into a single dictionary.

    Args:
        *dicts: Variable number of dictionaries to merge.

    Returns:
        Merged dictionary.
    """
    result: dict = {}
    for d in dicts:
        result.update(d)
    return result
