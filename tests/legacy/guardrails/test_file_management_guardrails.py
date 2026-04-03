"""Guardrails for centralized file management through DataManager."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCOPES = [
    ROOT / "src" / "graph",
    ROOT / "src" / "core" / "ai",
    ROOT / "src" / "core" / "tools",
]
BANNED_SNIPPETS = [
    ".read_text(",
    ".read_bytes(",
    ".write_text(",
    ".write_bytes(",
    ".mkdir(",
]


def test_runtime_code_uses_data_manager_for_file_io() -> None:
    violations: list[str] = []

    for scope in SCOPES:
        for path in scope.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for snippet in BANNED_SNIPPETS:
                if snippet in text:
                    violations.append(f"{path.relative_to(ROOT)} contains {snippet}")

    assert violations == []
