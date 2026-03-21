from __future__ import annotations

import base64
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.interfaces.api.config import load_settings

router = APIRouter(prefix="/api/v1/explorer", tags=["explorer"])

MAX_FILE_SIZE = 512 * 1024  # 512 KB preview limit
PREVIEWABLE_EXTENSIONS = {".json", ".md", ".txt", ".yaml", ".yml", ".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg"}

MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}


@router.get("/browse")
def browse(path: str = Query("", description="Relative path within data root")) -> dict:
    """List directory contents or return file preview."""
    settings = load_settings()
    data_root = Path(settings.data_root).resolve()
    target = (data_root / path).resolve()

    if not target.is_relative_to(data_root):
        raise HTTPException(status_code=403, detail="path traversal not allowed")

    if not target.exists():
        raise HTTPException(status_code=404, detail="path not found")

    if target.is_file():
        return _read_file(target, data_root)

    return _list_directory(target, data_root, path)


def _list_directory(target: Path, data_root: Path, path: str) -> dict:
    entries = []
    for child in sorted(target.iterdir()):
        rel = child.relative_to(data_root)
        entry: dict = {
            "name": child.name,
            "path": str(rel),
            "is_dir": child.is_dir(),
        }
        if child.is_file():
            entry["size_bytes"] = child.stat().st_size
            entry["extension"] = child.suffix.lower()
        elif child.is_dir():
            try:
                entry["child_count"] = sum(1 for _ in child.iterdir())
            except PermissionError:
                entry["child_count"] = 0
        entries.append(entry)

    entries.sort(key=lambda e: (not e["is_dir"], e["name"]))

    return {
        "path": path or ".",
        "is_dir": True,
        "entries": entries,
    }


def _read_file(target: Path, data_root: Path) -> dict:
    rel = str(target.relative_to(data_root))
    ext = target.suffix.lower()
    size = target.stat().st_size

    result: dict = {
        "path": rel,
        "is_dir": False,
        "name": target.name,
        "extension": ext,
        "size_bytes": size,
    }

    if ext in IMAGE_EXTENSIONS and size <= MAX_FILE_SIZE:
        raw = target.read_bytes()
        mime = MIME_MAP.get(ext, "application/octet-stream")
        result["content_type"] = "image"
        result["content"] = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
        return result

    if ext not in PREVIEWABLE_EXTENSIONS:
        result["content_type"] = "binary"
        result["content"] = None
        return result

    if size > MAX_FILE_SIZE:
        result["content_type"] = "too_large"
        result["content"] = None
        return result

    text = target.read_text(errors="replace")
    result["content_type"] = "text"
    result["content"] = text
    return result
