"""Helpers for parsing render metadata from CLI inputs."""

from __future__ import annotations


def parse_extra_vars(items: list[str]) -> dict[str, str]:
    """Parse repeated ``KEY=VALUE`` CLI metadata flags."""

    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid extra var '{item}'. Expected KEY=VALUE")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid extra var '{item}'. Empty key")
        parsed[key] = value.strip()
    return parsed
