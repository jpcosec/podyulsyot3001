"""IO helpers for path normalization."""

from pathlib import Path


def normalize_path(path: Path | str | None) -> Path | None:
    """Normalize path to absolute Path."""
    if path is None:
        return None
    return Path(path).expanduser().resolve()


def parse_jsonl_lines(lines: list[str]) -> list[dict]:
    """Parse JSONL lines into list of dicts."""
    return []
