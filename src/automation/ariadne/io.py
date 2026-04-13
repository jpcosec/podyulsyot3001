"""Shared file I/O helpers for Ariadne modules."""

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Any

import aiofiles


def _normalize_path(path: Path | str) -> Path:
    return Path(path)


def append_jsonl(path: Path | str, event: dict[str, Any]) -> Path:
    """Append one JSON event to a JSONL file."""
    file_path = _normalize_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return file_path


async def append_jsonl_async(path: Path | str, event: dict[str, Any]) -> Path:
    """Append one JSON event to a JSONL file asynchronously."""
    file_path = _normalize_path(path)
    await asyncio.to_thread(file_path.parent.mkdir, parents=True, exist_ok=True)
    async with aiofiles.open(file_path, "a", encoding="utf-8") as handle:
        await handle.write(json.dumps(event, sort_keys=True) + "\n")
    return file_path


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    """Read a JSONL file, returning an empty list when missing."""
    file_path = _normalize_path(path)
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


async def read_jsonl_async(path: Path | str) -> list[dict[str, Any]]:
    """Read a JSONL file asynchronously, returning an empty list when missing."""
    file_path = _normalize_path(path)
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as handle:
            lines = await handle.readlines()
    except FileNotFoundError:
        return []

    return await asyncio.to_thread(_parse_jsonl_lines, lines)


def read_json(path: Path | str) -> Any:
    """Read a JSON file synchronously."""
    file_path = _normalize_path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


async def read_json_async(path: Path | str) -> Any:
    """Read a JSON file asynchronously."""
    file_path = _normalize_path(path)
    async with aiofiles.open(file_path, "r", encoding="utf-8") as handle:
        content = await handle.read()
    return await asyncio.to_thread(json.loads, content)


def write_json(path: Path | str, payload: Any, *, indent: int = 2) -> Path:
    """Write a JSON file synchronously."""
    file_path = _normalize_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=indent)
    return file_path


async def write_json_async(path: Path | str, payload: Any, *, indent: int = 2) -> Path:
    """Write a JSON file asynchronously."""
    file_path = _normalize_path(path)
    await asyncio.to_thread(file_path.parent.mkdir, parents=True, exist_ok=True)
    content = await asyncio.to_thread(json.dumps, payload, indent=indent)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as handle:
        await handle.write(content)
    return file_path


def _parse_jsonl_lines(lines: list[str]) -> list[dict[str, Any]]:
    return [json.loads(line) for line in lines if line.strip()]
