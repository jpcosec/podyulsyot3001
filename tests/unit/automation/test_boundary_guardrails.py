"""AST-based import boundary guardrail.

Enforces the Ariadne dependency rule:
  ariadne/ (domain) → portals/ + motors/ (adapters) → execution libs

No layer may import from a layer above it in the hierarchy.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path("src/automation")

# Each entry: layer_path → list of forbidden import prefixes
RULES: dict[str, list[str]] = {
    "ariadne": [
        "src.automation.motors",
        "src.automation.portals",
    ],
    "portals": [
        "src.automation.motors",
    ],
    "motors/crawl4ai": [
        "src.automation.portals",
    ],
    "motors/browseros": [
        "src.automation.portals",
    ],
}


def _collect_imports(path: Path) -> list[str]:
    """Return all import module strings found in a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _find_violations(layer: str, forbidden: list[str]) -> list[str]:
    layer_path = SRC / layer
    if not layer_path.exists():
        return []
    violations: list[str] = []
    for py_file in sorted(layer_path.rglob("*.py")):
        for imp in _collect_imports(py_file):
            for prefix in forbidden:
                if imp == prefix or imp.startswith(prefix + "."):
                    rel = py_file.relative_to(SRC)
                    violations.append(f"  {rel}: imports '{imp}' (forbidden: '{prefix}')")
    return violations


@pytest.mark.parametrize("layer,forbidden", RULES.items())
def test_layer_does_not_import_forbidden(layer: str, forbidden: list[str]) -> None:
    violations = _find_violations(layer, forbidden)
    assert not violations, (
        f"Layer boundary violations in 'src/automation/{layer}':\n"
        + "\n".join(violations)
    )
