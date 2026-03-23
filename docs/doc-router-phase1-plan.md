# Doc-Router Phase 1: Scanner + Graph Builder + CLI + Graph Explorer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation — a CLI that scans tagged docs and code, builds a navigable graph, validates tags, and serves an interactive graph explorer UI.

**Architecture:** Python CLI (`click`) scans project files for tag annotations (YAML frontmatter in docs, structured docstrings in code). Parsed tags become a `RouteGraph` (nodes + edges) stored as JSON. FastAPI serves the graph to a React Flow UI. The UI reuses the Terran Command design system and graph components from PhD review-workbench.

**Tech Stack:**
- Backend: Python 3.11+, click (CLI), FastAPI (serve), PyYAML, hashlib
- Frontend: React 18, @xyflow/react 12, @dagrejs/dagre, Tailwind v4, CodeMirror (preview only)
- Testing: pytest, vitest
- Source reference: `apps/review-workbench/` in `ui-redesign` worktree

**Spec:** `docs/doc-router-design.md` (Sections 1, 2.1, 3, 4.1)

---

## File Structure

### Backend (`src/doc_router/`)

```
src/doc_router/
  __init__.py              # Package init, version
  cli.py                   # Click CLI entrypoint (init, scan, lint, graph, serve)
  config.py                # Load/validate doc-router.yml
  models.py                # TaggedEntity, RouteNode, RouteEdge, RouteGraph dataclasses
  scanner/
    __init__.py
    markdown.py            # Parse YAML frontmatter from .md files
    python.py              # Parse :doc-*: from Python docstrings
    typescript.py           # Parse @doc-* from JSDoc (stub for Phase 1)
    registry.py            # Scanner registry — maps file extensions to parsers
  graph.py                 # Graph builder — resolve references, detect broken links, compute stats
  linter.py                # Validate tags against vocabulary, check required fields
  server.py                # FastAPI app — serve graph JSON + static UI
```

### Frontend (`ui/`)

```
ui/
  package.json
  vite.config.ts
  tsconfig.json
  tsconfig.app.json
  index.html
  src/
    main.tsx               # React root
    App.tsx                 # Router (single route: graph explorer)
    styles.css             # Terran Command design system (copied from review-workbench)
    utils/cn.ts            # Class merge utility (copied)
    api/
      client.ts            # Fetch graph from FastAPI backend
    types/
      graph.types.ts       # RouteNode, RouteEdge, RouteGraph TypeScript types
    components/
      atoms/
        Badge.tsx           # Copied from review-workbench
        Button.tsx          # Copied from review-workbench
        Icon.tsx            # Copied from review-workbench
        Spinner.tsx         # Copied from review-workbench
        Tag.tsx             # Copied from review-workbench
      molecules/
        ControlPanel.tsx    # Adapted — show node tags, linked files
        SplitPane.tsx       # Copied from review-workbench
      layouts/
        AppShell.tsx        # Simplified — doc-router branding, no job nav
    features/
      graph-explorer/
        components/
          RouteGraphCanvas.tsx    # React Flow canvas for route graph
          DocNode.tsx             # Custom node for doc-type entities
          CodeNode.tsx            # Custom node for code-type entities
          RouteEdge.tsx           # Custom edge with type label
          NodeInspector.tsx       # Right panel — show node details on click
          FilterBar.tsx           # Domain/stage/nature filter controls
        hooks/
          useRouteGraph.ts        # TanStack Query hook — fetch + filter graph
        lib/
          layout.ts              # Dagre layout for route graph
          colors.ts              # Domain → hue mapping
```

### Tests

```
tests/
  conftest.py                    # Fixtures: sample doc-router.yml, sample tagged files
  test_config.py                 # Config loading/validation
  test_scanner_markdown.py       # Frontmatter parsing
  test_scanner_python.py         # Docstring tag parsing
  test_graph.py                  # Graph building, broken link detection
  test_linter.py                 # Vocabulary validation, required fields
  test_cli.py                    # CLI integration tests (click.testing.CliRunner)
  test_server.py                 # FastAPI endpoint tests
  fixtures/
    sample_project/
      doc-router.yml             # Sample config
      docs/
        design.md                # Tagged doc (frontmatter)
        architecture.md          # Tagged doc (depends_on)
      src/
        module.py                # Tagged Python file (docstrings)
        empty.py                 # No tags (orphan)
```

### Root

```
doc-router.yml                   # PhD 2.0 project config (first consumer)
pyproject.toml                   # Package config, CLI entrypoint
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/doc_router/__init__.py`
- Create: `src/doc_router/cli.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
sources = ["src"]

[project]
name = "doc-router"
version = "0.1.0"
description = "Documentation-driven development framework"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
    "fastapi>=0.111",
    "uvicorn>=0.30",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
]

[project.scripts]
doc-router = "doc_router.cli:cli"
```

- [ ] **Step 2: Create package init**

```python
# src/doc_router/__init__.py
"""Doc-Router: Documentation-driven development framework."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create minimal CLI**

```python
# src/doc_router/cli.py
"""CLI entrypoint for doc-router."""

import click

from doc_router import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Documentation-driven development framework."""


@cli.command()
def init() -> None:
    """Create doc-router.yml and templates directory."""
    click.echo("doc-router init — not yet implemented")
```

- [ ] **Step 4: Install and verify**

Run: `pip install -e ".[dev]"`
Run: `doc-router --version`
Expected: `doc-router, version 0.1.0`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/doc_router/__init__.py src/doc_router/cli.py
git commit -m "feat(doc-router): scaffold project with CLI entrypoint"
```

---

## Task 2: Config Model

**Files:**
- Create: `src/doc_router/config.py`
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`
- Create: `tests/fixtures/sample_project/doc-router.yml`

- [ ] **Step 1: Create sample config fixture**

```yaml
# tests/fixtures/sample_project/doc-router.yml
project: sample-project
domains: [ui, api, pipeline, core]
stages: [scrape, extract, match, render]
natures: [philosophy, implementation, development, testing]
doc_paths:
  central: docs/
  plans: plan/
source_paths:
  - src/
```

- [ ] **Step 2: Create conftest with fixtures**

```python
# tests/conftest.py
"""Shared test fixtures."""

from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_project_dir() -> Path:
    return FIXTURES_DIR / "sample_project"


@pytest.fixture
def sample_config_path(sample_project_dir: Path) -> Path:
    return sample_project_dir / "doc-router.yml"
```

- [ ] **Step 3: Write failing test for config loading**

```python
# tests/test_config.py
"""Tests for config loading and validation."""

from pathlib import Path

from doc_router.config import DocRouterConfig, load_config


def test_load_valid_config(sample_config_path: Path) -> None:
    config = load_config(sample_config_path)
    assert config.project == "sample-project"
    assert "pipeline" in config.domains
    assert "match" in config.stages
    assert "philosophy" in config.natures
    assert config.doc_paths["central"] == "docs/"
    assert config.source_paths == ["src/"]


def test_load_config_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "doc-router.yml"
    try:
        load_config(missing)
        assert False, "Should have raised"
    except FileNotFoundError:
        pass


def test_config_validates_required_fields(tmp_path: Path) -> None:
    bad_config = tmp_path / "doc-router.yml"
    bad_config.write_text("project: test\n")
    try:
        load_config(bad_config)
        assert False, "Should have raised"
    except ValueError as e:
        assert "domains" in str(e)
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'doc_router.config'`

- [ ] **Step 5: Implement config module**

```python
# src/doc_router/config.py
"""Load and validate doc-router.yml configuration."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


_REQUIRED_FIELDS = ("project", "domains", "stages", "natures")


@dataclass(frozen=True)
class DocRouterConfig:
    project: str
    domains: list[str]
    stages: list[str]
    natures: list[str]
    doc_paths: dict[str, str] = field(default_factory=lambda: {"central": "docs/"})
    source_paths: list[str] = field(default_factory=lambda: ["src/"])
    template_paths: dict[str, str] = field(default_factory=dict)


def load_config(path: Path) -> DocRouterConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")

    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid config format in {path}")

    missing = [f for f in _REQUIRED_FIELDS if f not in raw]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    return DocRouterConfig(
        project=raw["project"],
        domains=raw["domains"],
        stages=raw["stages"],
        natures=raw["natures"],
        doc_paths=raw.get("doc_paths", {"central": "docs/"}),
        source_paths=raw.get("source_paths", ["src/"]),
        template_paths=raw.get("templates", {}),
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add src/doc_router/config.py tests/conftest.py tests/test_config.py tests/fixtures/
git commit -m "feat(doc-router): config loading and validation"
```

---

## Task 3: Data Models

**Files:**
- Create: `src/doc_router/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for models**

```python
# tests/test_models.py
"""Tests for core data models."""

from doc_router.models import RouteNode, RouteEdge, RouteGraph


def test_route_node_creation() -> None:
    node = RouteNode(
        id="pipeline-match-design",
        type="doc",
        path="docs/product/match.md",
        domain="pipeline",
        stage="match",
        nature="philosophy",
        version="2026-03-22",
    )
    assert node.id == "pipeline-match-design"
    assert node.type == "doc"
    assert node.symbol is None


def test_route_node_code_with_symbol() -> None:
    node = RouteNode(
        id="pipeline-match-impl",
        type="code",
        path="src/nodes/match/logic.py",
        domain="pipeline",
        stage="match",
        nature="implementation",
        symbol="MatchLogic",
        tags={"hitl_gate": "review_match", "contract": "src/nodes/match/contract.py::MatchInput"},
    )
    assert node.symbol == "MatchLogic"
    assert node.tags["hitl_gate"] == "review_match"


def test_route_graph_serialization() -> None:
    node = RouteNode(
        id="test-node",
        type="doc",
        path="docs/test.md",
        domain="core",
        nature="philosophy",
    )
    edge = RouteEdge(source="test-node", target="other-node", type="depends_on")
    graph = RouteGraph(nodes=[node], edges=[edge])

    data = graph.to_dict()
    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 1
    assert data["nodes"][0]["id"] == "test-node"

    restored = RouteGraph.from_dict(data)
    assert restored.nodes[0].id == "test-node"
    assert restored.edges[0].type == "depends_on"


def test_route_graph_filter_by_domain() -> None:
    nodes = [
        RouteNode(id="a", type="doc", path="a.md", domain="ui", nature="impl"),
        RouteNode(id="b", type="doc", path="b.md", domain="pipeline", nature="impl"),
    ]
    graph = RouteGraph(nodes=nodes, edges=[])
    filtered = graph.filter(domain="ui")
    assert len(filtered.nodes) == 1
    assert filtered.nodes[0].id == "a"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement models**

```python
# src/doc_router/models.py
"""Core data models for the route graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RouteNode:
    id: str
    type: str  # "doc" or "code"
    path: str
    domain: str
    nature: str
    stage: str = "global"
    version: str | None = None
    symbol: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "path": self.path,
            "domain": self.domain,
            "stage": self.stage,
            "nature": self.nature,
            "version": self.version,
            "symbol": self.symbol,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteNode:
        return cls(**data)


@dataclass
class RouteEdge:
    source: str
    target: str
    type: str  # "implements", "doc-ref", "depends_on", "contract"

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "target": self.target, "type": self.type}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteEdge:
        return cls(**data)


@dataclass
class RouteGraph:
    nodes: list[RouteNode]
    edges: list[RouteEdge]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RouteGraph:
        return cls(
            nodes=[RouteNode.from_dict(n) for n in data["nodes"]],
            edges=[RouteEdge.from_dict(e) for e in data["edges"]],
        )

    def filter(
        self,
        domain: str | None = None,
        stage: str | None = None,
        nature: str | None = None,
    ) -> RouteGraph:
        filtered = self.nodes
        if domain:
            filtered = [n for n in filtered if n.domain == domain]
        if stage:
            filtered = [n for n in filtered if n.stage == stage]
        if nature:
            filtered = [n for n in filtered if n.nature == nature]
        node_ids = {n.id for n in filtered}
        edges = [e for e in self.edges if e.source in node_ids or e.target in node_ids]
        return RouteGraph(nodes=filtered, edges=edges)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/doc_router/models.py tests/test_models.py
git commit -m "feat(doc-router): core data models for route graph"
```

---

## Task 4: Markdown Scanner

**Files:**
- Create: `src/doc_router/scanner/__init__.py`
- Create: `src/doc_router/scanner/markdown.py`
- Create: `tests/fixtures/sample_project/docs/design.md`
- Create: `tests/fixtures/sample_project/docs/architecture.md`
- Create: `tests/test_scanner_markdown.py`

- [ ] **Step 1: Create tagged markdown fixtures**

```markdown
<!-- tests/fixtures/sample_project/docs/design.md -->
---
id: pipeline-match-design
domain: pipeline
stage: match
nature: philosophy
implements:
  - src/module.py
  - src/module.py::MatchLogic
depends_on:
  - core-architecture
version: 2026-03-22
---

# Match Stage Design

This document describes the match stage.
```

```markdown
<!-- tests/fixtures/sample_project/docs/architecture.md -->
---
id: core-architecture
domain: core
nature: philosophy
version: 2026-03-20
---

# System Architecture

Core architecture document.
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_scanner_markdown.py
"""Tests for markdown frontmatter scanner."""

from pathlib import Path

from doc_router.scanner.markdown import scan_markdown_file, scan_markdown_dir


def test_scan_single_file(sample_project_dir: Path) -> None:
    doc = sample_project_dir / "docs" / "design.md"
    nodes, edges = scan_markdown_file(doc, sample_project_dir)
    assert len(nodes) == 1
    node = nodes[0]
    assert node.id == "pipeline-match-design"
    assert node.domain == "pipeline"
    assert node.stage == "match"
    assert node.nature == "philosophy"
    assert node.type == "doc"
    assert node.version == "2026-03-22"
    # implements → edges
    assert len(edges) >= 1
    impl_edges = [e for e in edges if e.type == "implements"]
    assert len(impl_edges) == 2
    dep_edges = [e for e in edges if e.type == "depends_on"]
    assert len(dep_edges) == 1
    assert dep_edges[0].target == "core-architecture"


def test_scan_file_without_frontmatter(tmp_path: Path) -> None:
    doc = tmp_path / "plain.md"
    doc.write_text("# No Frontmatter\n\nJust text.\n")
    nodes, edges = scan_markdown_file(doc, tmp_path)
    assert len(nodes) == 0
    assert len(edges) == 0


def test_scan_file_missing_required_fields(tmp_path: Path) -> None:
    doc = tmp_path / "bad.md"
    doc.write_text("---\ndomain: ui\n---\n# Missing id and nature\n")
    nodes, edges = scan_markdown_file(doc, tmp_path)
    # Should return empty (skip invalid) not crash
    assert len(nodes) == 0


def test_scan_directory(sample_project_dir: Path) -> None:
    docs_dir = sample_project_dir / "docs"
    nodes, edges = scan_markdown_dir(docs_dir, sample_project_dir)
    assert len(nodes) == 2  # design.md + architecture.md
    ids = {n.id for n in nodes}
    assert "pipeline-match-design" in ids
    assert "core-architecture" in ids
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_scanner_markdown.py -v`
Expected: FAIL

- [ ] **Step 4: Implement markdown scanner**

```python
# src/doc_router/scanner/__init__.py
"""File scanners for extracting doc-router tags."""

# src/doc_router/scanner/markdown.py
"""Parse YAML frontmatter from markdown files."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from doc_router.models import RouteEdge, RouteNode

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ("id", "domain", "nature")


def scan_markdown_file(
    path: Path, project_root: Path
) -> tuple[list[RouteNode], list[RouteEdge]]:
    text = path.read_text(encoding="utf-8")
    frontmatter = _extract_frontmatter(text)
    if frontmatter is None:
        return [], []

    missing = [f for f in _REQUIRED_FIELDS if f not in frontmatter]
    if missing:
        logger.warning("Skipping %s: missing fields %s", path, missing)
        return [], []

    rel_path = str(path.relative_to(project_root))
    node_id = frontmatter["id"]

    node = RouteNode(
        id=node_id,
        type="doc",
        path=rel_path,
        domain=frontmatter["domain"],
        stage=frontmatter.get("stage", "global"),
        nature=frontmatter["nature"],
        version=str(frontmatter["version"]) if frontmatter.get("version") else None,
    )

    edges: list[RouteEdge] = []
    for target in frontmatter.get("implements", []):
        edges.append(RouteEdge(source=node_id, target=str(target), type="implements"))
    for target in frontmatter.get("depends_on", []):
        edges.append(RouteEdge(source=node_id, target=str(target), type="depends_on"))

    return [node], edges


def scan_markdown_dir(
    directory: Path, project_root: Path
) -> tuple[list[RouteNode], list[RouteEdge]]:
    all_nodes: list[RouteNode] = []
    all_edges: list[RouteEdge] = []
    for md_file in sorted(directory.rglob("*.md")):
        nodes, edges = scan_markdown_file(md_file, project_root)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
    return all_nodes, all_edges


def _extract_frontmatter(text: str) -> dict | None:
    stripped = text.strip()
    if not stripped.startswith("---"):
        return None
    end = stripped.find("---", 3)
    if end == -1:
        return None
    raw = stripped[3:end].strip()
    try:
        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else None
    except yaml.YAMLError:
        return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_scanner_markdown.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/doc_router/scanner/ tests/test_scanner_markdown.py tests/fixtures/sample_project/docs/
git commit -m "feat(doc-router): markdown frontmatter scanner"
```

---

## Task 5: Python Docstring Scanner

**Files:**
- Create: `src/doc_router/scanner/python.py`
- Create: `tests/fixtures/sample_project/src/module.py`
- Create: `tests/fixtures/sample_project/src/empty.py`
- Create: `tests/test_scanner_python.py`

- [ ] **Step 1: Create tagged Python fixture**

```python
# tests/fixtures/sample_project/src/module.py
"""Sample module with doc-router tags."""


class MatchLogic:
    """Aligns candidate evidence to job requirements.

    :doc-id: pipeline-match-impl
    :domain: pipeline
    :stage: match
    :nature: implementation
    :doc-ref: pipeline-match-design
    :contract: src/nodes/match/contract.py::MatchInput
    :hitl-gate: review_match
    """

    def run(self) -> None:
        pass


class HelperClass:
    """A helper with no doc-router tags."""

    pass
```

```python
# tests/fixtures/sample_project/src/empty.py
"""Module with no doc-router tags."""


def utility() -> None:
    pass
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_scanner_python.py
"""Tests for Python docstring scanner."""

from pathlib import Path

from doc_router.scanner.python import scan_python_file, scan_python_dir


def test_scan_tagged_class(sample_project_dir: Path) -> None:
    py_file = sample_project_dir / "src" / "module.py"
    nodes, edges = scan_python_file(py_file, sample_project_dir)
    assert len(nodes) == 1
    node = nodes[0]
    assert node.id == "pipeline-match-impl"
    assert node.type == "code"
    assert node.symbol == "MatchLogic"
    assert node.domain == "pipeline"
    assert node.stage == "match"
    assert node.tags["hitl_gate"] == "review_match"
    # doc-ref → edge
    ref_edges = [e for e in edges if e.type == "doc-ref"]
    assert len(ref_edges) == 1
    assert ref_edges[0].target == "pipeline-match-design"


def test_scan_file_without_tags(sample_project_dir: Path) -> None:
    py_file = sample_project_dir / "src" / "empty.py"
    nodes, edges = scan_python_file(py_file, sample_project_dir)
    assert len(nodes) == 0


def test_scan_python_dir(sample_project_dir: Path) -> None:
    src_dir = sample_project_dir / "src"
    nodes, edges = scan_python_dir(src_dir, sample_project_dir)
    assert len(nodes) == 1  # Only MatchLogic has tags
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_scanner_python.py -v`
Expected: FAIL

- [ ] **Step 4: Implement Python scanner**

```python
# src/doc_router/scanner/python.py
"""Parse :doc-*: tags from Python docstrings."""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

from doc_router.models import RouteEdge, RouteNode

logger = logging.getLogger(__name__)

_TAG_PATTERN = re.compile(r":(\w[\w-]*):\s*(.+)")
_EDGE_TAGS = {"doc-ref": "doc-ref", "contract": "contract"}
_META_TAGS = {"hitl-gate": "hitl_gate", "contract": "contract"}


def scan_python_file(
    path: Path, project_root: Path
) -> tuple[list[RouteNode], list[RouteEdge]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        logger.warning("Could not parse %s", path)
        return [], []

    rel_path = str(path.relative_to(project_root))
    all_nodes: list[RouteNode] = []
    all_edges: list[RouteEdge] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        docstring = ast.get_docstring(node)
        if not docstring:
            continue
        tags = _parse_doc_tags(docstring)
        if "id" not in tags:
            continue

        node_id = tags["id"]
        route_node = RouteNode(
            id=node_id,
            type="code",
            path=rel_path,
            domain=tags.get("domain", "unknown"),
            stage=tags.get("stage", "global"),
            nature=tags.get("nature", "implementation"),
            symbol=node.name,
            tags={
                meta_key: tags[tag_name]
                for tag_name, meta_key in _META_TAGS.items()
                if tag_name in tags
            },
        )
        all_nodes.append(route_node)

        if "doc-ref" in tags:
            all_edges.append(RouteEdge(source=node_id, target=tags["doc-ref"], type="doc-ref"))
        if "contract" in tags:
            all_edges.append(RouteEdge(source=node_id, target=tags["contract"], type="contract"))

    return all_nodes, all_edges


def scan_python_dir(
    directory: Path, project_root: Path
) -> tuple[list[RouteNode], list[RouteEdge]]:
    all_nodes: list[RouteNode] = []
    all_edges: list[RouteEdge] = []
    for py_file in sorted(directory.rglob("*.py")):
        nodes, edges = scan_python_file(py_file, project_root)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
    return all_nodes, all_edges


def _parse_doc_tags(docstring: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for match in _TAG_PATTERN.finditer(docstring):
        key = match.group(1)
        value = match.group(2).strip()
        # Normalize: :doc-id: → "id", :doc-ref: stays as "doc-ref"
        if key == "doc-id":
            key = "id"
        tags[key] = value
    return tags
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_scanner_python.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/doc_router/scanner/python.py tests/test_scanner_python.py tests/fixtures/sample_project/src/
git commit -m "feat(doc-router): Python docstring tag scanner"
```

---

## Task 6: Scanner Registry

**Files:**
- Create: `src/doc_router/scanner/registry.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_scanner_python.py` or create a new file:

```python
# tests/test_scanner_registry.py
"""Tests for scanner registry."""

from pathlib import Path

from doc_router.scanner.registry import scan_project
from doc_router.config import load_config


def test_scan_project_finds_all_entities(sample_project_dir: Path) -> None:
    config = load_config(sample_project_dir / "doc-router.yml")
    nodes, edges = scan_project(sample_project_dir, config)
    # 2 docs (design.md, architecture.md) + 1 code (MatchLogic)
    assert len(nodes) == 3
    types = {n.type for n in nodes}
    assert types == {"doc", "code"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scanner_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Implement registry**

```python
# src/doc_router/scanner/registry.py
"""Scan a project by dispatching to file-type-specific scanners."""

from __future__ import annotations

from pathlib import Path

from doc_router.config import DocRouterConfig
from doc_router.models import RouteEdge, RouteNode
from doc_router.scanner.markdown import scan_markdown_dir
from doc_router.scanner.python import scan_python_dir


def scan_project(
    project_root: Path, config: DocRouterConfig
) -> tuple[list[RouteNode], list[RouteEdge]]:
    all_nodes: list[RouteNode] = []
    all_edges: list[RouteEdge] = []

    # Scan doc paths
    for doc_dir in config.doc_paths.values():
        full_path = project_root / doc_dir
        if full_path.is_dir():
            nodes, edges = scan_markdown_dir(full_path, project_root)
            all_nodes.extend(nodes)
            all_edges.extend(edges)

    # Scan source paths
    for src_dir in config.source_paths:
        full_path = project_root / src_dir
        if full_path.is_dir():
            nodes, edges = scan_python_dir(full_path, project_root)
            all_nodes.extend(nodes)
            all_edges.extend(edges)

    return all_nodes, all_edges
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_scanner_registry.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/doc_router/scanner/registry.py tests/test_scanner_registry.py
git commit -m "feat(doc-router): scanner registry dispatches by file type"
```

---

## Task 7: Graph Builder

**Files:**
- Create: `src/doc_router/graph.py`
- Create: `tests/test_graph.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_graph.py
"""Tests for graph builder."""

from pathlib import Path

from doc_router.config import load_config
from doc_router.graph import build_graph
from doc_router.scanner.registry import scan_project


def test_build_graph_resolves_edges(sample_project_dir: Path) -> None:
    config = load_config(sample_project_dir / "doc-router.yml")
    nodes, edges = scan_project(sample_project_dir, config)
    graph, issues = build_graph(nodes, edges)
    assert len(graph.nodes) == 3
    # depends_on edge from design → architecture (both exist)
    dep_edges = [e for e in graph.edges if e.type == "depends_on"]
    assert len(dep_edges) == 1


def test_build_graph_detects_broken_implements(sample_project_dir: Path) -> None:
    config = load_config(sample_project_dir / "doc-router.yml")
    nodes, edges = scan_project(sample_project_dir, config)
    # design.md implements src/module.py — but the edge target is a path, not a node id
    # The builder should resolve path-based targets or flag them
    graph, issues = build_graph(nodes, edges)
    broken = [i for i in issues if i["type"] == "broken_link"]
    # src/module.py exists as a file but "src/module.py" is not a node id
    # The implements edge target "src/module.py::MatchLogic" should resolve to pipeline-match-impl
    # The bare "src/module.py" cannot resolve to a single node → broken
    assert any("src/module.py" in str(i.get("target", "")) for i in broken)


def test_build_graph_detects_duplicate_ids() -> None:
    from doc_router.models import RouteNode, RouteEdge

    nodes = [
        RouteNode(id="dup", type="doc", path="a.md", domain="ui", nature="impl"),
        RouteNode(id="dup", type="doc", path="b.md", domain="ui", nature="impl"),
    ]
    graph, issues = build_graph(nodes, [])
    dups = [i for i in issues if i["type"] == "duplicate_id"]
    assert len(dups) == 1


def test_build_graph_stats() -> None:
    from doc_router.models import RouteNode

    nodes = [
        RouteNode(id="a", type="doc", path="a.md", domain="ui", nature="impl"),
        RouteNode(id="b", type="code", path="b.py", domain="pipeline", nature="impl"),
    ]
    graph, issues = build_graph(nodes, [])
    assert len(graph.nodes) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_graph.py -v`
Expected: FAIL

- [ ] **Step 3: Implement graph builder**

```python
# src/doc_router/graph.py
"""Build and validate the route graph from scanned entities."""

from __future__ import annotations

from doc_router.models import RouteEdge, RouteGraph, RouteNode

Issue = dict[str, str]


def build_graph(
    nodes: list[RouteNode],
    edges: list[RouteEdge],
) -> tuple[RouteGraph, list[Issue]]:
    issues: list[Issue] = []

    # Check duplicate IDs
    seen_ids: dict[str, str] = {}
    unique_nodes: list[RouteNode] = []
    for node in nodes:
        if node.id in seen_ids:
            issues.append({
                "type": "duplicate_id",
                "id": node.id,
                "paths": f"{seen_ids[node.id]}, {node.path}",
            })
        else:
            seen_ids[node.id] = node.path
            unique_nodes.append(node)

    # Build path-to-id index for resolving implements targets
    path_to_ids: dict[str, list[str]] = {}
    for node in unique_nodes:
        key = node.path
        path_to_ids.setdefault(key, []).append(node.id)
        if node.symbol:
            symbol_key = f"{node.path}::{node.symbol}"
            path_to_ids.setdefault(symbol_key, []).append(node.id)

    # Resolve and validate edges
    resolved_edges: list[RouteEdge] = []
    node_ids = {n.id for n in unique_nodes}

    for edge in edges:
        target = edge.target
        if target in node_ids:
            resolved_edges.append(edge)
        elif target in path_to_ids:
            # Resolve path to node id(s)
            for resolved_id in path_to_ids[target]:
                resolved_edges.append(
                    RouteEdge(source=edge.source, target=resolved_id, type=edge.type)
                )
        else:
            issues.append({
                "type": "broken_link",
                "source": edge.source,
                "target": target,
                "edge_type": edge.type,
            })

    return RouteGraph(nodes=unique_nodes, edges=resolved_edges), issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_graph.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/doc_router/graph.py tests/test_graph.py
git commit -m "feat(doc-router): graph builder with edge resolution and validation"
```

---

## Task 8: Linter

**Files:**
- Create: `src/doc_router/linter.py`
- Create: `tests/test_linter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_linter.py
"""Tests for tag linter."""

from doc_router.config import DocRouterConfig
from doc_router.linter import lint_nodes
from doc_router.models import RouteNode


def _config() -> DocRouterConfig:
    return DocRouterConfig(
        project="test",
        domains=["ui", "pipeline"],
        stages=["match", "extract"],
        natures=["philosophy", "implementation"],
    )


def test_lint_valid_node() -> None:
    node = RouteNode(id="a", type="doc", path="a.md", domain="pipeline", stage="match", nature="philosophy")
    issues = lint_nodes([node], _config())
    assert len(issues) == 0


def test_lint_invalid_domain() -> None:
    node = RouteNode(id="a", type="doc", path="a.md", domain="WRONG", nature="philosophy")
    issues = lint_nodes([node], _config())
    assert len(issues) == 1
    assert issues[0]["type"] == "invalid_domain"


def test_lint_invalid_stage() -> None:
    node = RouteNode(id="a", type="doc", path="a.md", domain="ui", stage="WRONG", nature="philosophy")
    issues = lint_nodes([node], _config())
    assert len(issues) == 1
    assert issues[0]["type"] == "invalid_stage"


def test_lint_global_stage_always_valid() -> None:
    node = RouteNode(id="a", type="doc", path="a.md", domain="ui", stage="global", nature="philosophy")
    issues = lint_nodes([node], _config())
    assert len(issues) == 0


def test_lint_invalid_nature() -> None:
    node = RouteNode(id="a", type="doc", path="a.md", domain="ui", nature="WRONG")
    issues = lint_nodes([node], _config())
    assert len(issues) == 1
    assert issues[0]["type"] == "invalid_nature"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_linter.py -v`
Expected: FAIL

- [ ] **Step 3: Implement linter**

```python
# src/doc_router/linter.py
"""Validate tags against project vocabulary."""

from __future__ import annotations

from doc_router.config import DocRouterConfig
from doc_router.models import RouteNode

Issue = dict[str, str]


def lint_nodes(nodes: list[RouteNode], config: DocRouterConfig) -> list[Issue]:
    issues: list[Issue] = []
    valid_domains = set(config.domains)
    valid_stages = set(config.stages) | {"global"}
    valid_natures = set(config.natures)

    for node in nodes:
        if node.domain not in valid_domains:
            issues.append({
                "type": "invalid_domain",
                "node_id": node.id,
                "path": node.path,
                "value": node.domain,
                "valid": ", ".join(sorted(valid_domains)),
            })
        if node.stage not in valid_stages:
            issues.append({
                "type": "invalid_stage",
                "node_id": node.id,
                "path": node.path,
                "value": node.stage,
                "valid": ", ".join(sorted(valid_stages)),
            })
        if node.nature not in valid_natures:
            issues.append({
                "type": "invalid_nature",
                "node_id": node.id,
                "path": node.path,
                "value": node.nature,
                "valid": ", ".join(sorted(valid_natures)),
            })

    return issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_linter.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/doc_router/linter.py tests/test_linter.py
git commit -m "feat(doc-router): vocabulary linter for tag validation"
```

---

## Task 9: CLI Commands (scan, lint, graph)

**Files:**
- Modify: `src/doc_router/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
"""Tests for CLI commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from doc_router.cli import cli


def test_cli_scan(sample_project_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", "--project", str(sample_project_dir)])
    assert result.exit_code == 0
    assert "3 nodes" in result.output


def test_cli_scan_json(sample_project_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", "--project", str(sample_project_dir), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data
    assert len(data["nodes"]) == 3


def test_cli_lint(sample_project_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", "--project", str(sample_project_dir)])
    assert result.exit_code == 0


def test_cli_graph_text(sample_project_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["graph", "--project", str(sample_project_dir)])
    assert result.exit_code == 0
    assert "pipeline-match-design" in result.output


def test_cli_graph_filter(sample_project_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [
        "graph", "--project", str(sample_project_dir),
        "--domain", "core",
    ])
    assert result.exit_code == 0
    assert "core-architecture" in result.output
    assert "pipeline-match-design" not in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Implement CLI commands**

```python
# src/doc_router/cli.py
"""CLI entrypoint for doc-router."""

from __future__ import annotations

import json
from pathlib import Path

import click

from doc_router import __version__
from doc_router.config import load_config
from doc_router.graph import build_graph
from doc_router.linter import lint_nodes
from doc_router.scanner.registry import scan_project


def _find_config(project: str | None) -> Path:
    root = Path(project) if project else Path.cwd()
    config_path = root / "doc-router.yml"
    if not config_path.exists():
        raise click.ClickException(f"No doc-router.yml found in {root}")
    return config_path


def _scan_and_build(project: str | None):
    config_path = _find_config(project)
    project_root = config_path.parent
    config = load_config(config_path)
    nodes, edges = scan_project(project_root, config)
    graph, build_issues = build_graph(nodes, edges)
    return project_root, config, graph, build_issues


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Documentation-driven development framework."""


@cli.command()
@click.option("--project", default=None, help="Project root (default: cwd)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def scan(project: str | None, as_json: bool) -> None:
    """Scan project and build route graph."""
    _, _, graph, issues = _scan_and_build(project)
    if as_json:
        click.echo(json.dumps(graph.to_dict(), indent=2))
    else:
        doc_count = sum(1 for n in graph.nodes if n.type == "doc")
        code_count = sum(1 for n in graph.nodes if n.type == "code")
        click.echo(f"Scanned: {len(graph.nodes)} nodes ({doc_count} docs, {code_count} code), {len(graph.edges)} edges")
        if issues:
            click.echo(f"Issues: {len(issues)}")
            for issue in issues:
                click.echo(f"  [{issue['type']}] {issue}")


@cli.command()
@click.option("--project", default=None, help="Project root (default: cwd)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def lint(project: str | None, as_json: bool) -> None:
    """Validate tags against project vocabulary."""
    config_path = _find_config(project)
    config = load_config(config_path)
    nodes, _ = scan_project(config_path.parent, config)
    issues = lint_nodes(nodes, config)
    if as_json:
        click.echo(json.dumps(issues, indent=2))
    elif issues:
        click.echo(f"Lint issues: {len(issues)}")
        for issue in issues:
            click.echo(f"  [{issue['type']}] {issue['node_id']} in {issue['path']}: "
                       f"'{issue['value']}' not in [{issue['valid']}]")
        raise SystemExit(1)
    else:
        click.echo("Lint: all tags valid")


@cli.command()
@click.option("--project", default=None, help="Project root (default: cwd)")
@click.option("--domain", default=None, help="Filter by domain")
@click.option("--stage", default=None, help="Filter by stage")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def graph(project: str | None, domain: str | None, stage: str | None, as_json: bool) -> None:
    """Print or export the route graph."""
    _, _, full_graph, _ = _scan_and_build(project)
    filtered = full_graph.filter(domain=domain, stage=stage)

    if as_json:
        click.echo(json.dumps(filtered.to_dict(), indent=2))
    else:
        click.echo(f"Nodes ({len(filtered.nodes)}):")
        for node in filtered.nodes:
            symbol = f"::{node.symbol}" if node.symbol else ""
            click.echo(f"  [{node.domain}/{node.stage}] {node.id} ({node.type}: {node.path}{symbol})")
        click.echo(f"\nEdges ({len(filtered.edges)}):")
        for edge in filtered.edges:
            click.echo(f"  {edge.source} --[{edge.type}]--> {edge.target}")


@cli.command()
def init() -> None:
    """Create doc-router.yml and templates directory."""
    click.echo("doc-router init — not yet implemented")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: 5 passed

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All passed (17 tests)

- [ ] **Step 6: Commit**

```bash
git add src/doc_router/cli.py tests/test_cli.py
git commit -m "feat(doc-router): CLI commands scan, lint, graph with JSON output"
```

---

## Task 10: FastAPI Server

**Files:**
- Create: `src/doc_router/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_server.py
"""Tests for FastAPI server."""

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from doc_router.server import create_app


@pytest.fixture
def app(sample_project_dir: Path):
    return create_app(project_root=sample_project_dir)


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_graph(client) -> None:
    resp = await client.get("/api/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 3


@pytest.mark.asyncio
async def test_get_graph_filtered(client) -> None:
    resp = await client.get("/api/graph", params={"domain": "core"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["domain"] == "core"


@pytest.mark.asyncio
async def test_get_stats(client) -> None:
    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_nodes" in data
    assert data["total_nodes"] == 3


@pytest.mark.asyncio
async def test_get_node_detail(client) -> None:
    resp = await client.get("/api/nodes/pipeline-match-design")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node"]["id"] == "pipeline-match-design"
    assert "connected_edges" in data


@pytest.mark.asyncio
async def test_get_node_not_found(client) -> None:
    resp = await client.get("/api/nodes/nonexistent")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_server.py -v`
Expected: FAIL

- [ ] **Step 3: Implement server**

```python
# src/doc_router/server.py
"""FastAPI server for doc-router graph API and static UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from doc_router.config import load_config
from doc_router.graph import build_graph
from doc_router.models import RouteGraph
from doc_router.scanner.registry import scan_project


def create_app(project_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Doc-Router", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Build graph on startup
    root = project_root or Path.cwd()
    config = load_config(root / "doc-router.yml")
    nodes, edges = scan_project(root, config)
    graph, issues = build_graph(nodes, edges)

    # Store in app state
    app.state.graph = graph
    app.state.issues = issues
    app.state.config = config

    @app.get("/api/graph")
    def get_graph(
        domain: str | None = None,
        stage: str | None = None,
        nature: str | None = None,
    ):
        filtered = app.state.graph.filter(domain=domain, stage=stage, nature=nature)
        return filtered.to_dict()

    @app.get("/api/stats")
    def get_stats():
        g: RouteGraph = app.state.graph
        return {
            "total_nodes": len(g.nodes),
            "doc_nodes": sum(1 for n in g.nodes if n.type == "doc"),
            "code_nodes": sum(1 for n in g.nodes if n.type == "code"),
            "total_edges": len(g.edges),
            "issues": len(app.state.issues),
            "domains": sorted({n.domain for n in g.nodes}),
            "stages": sorted({n.stage for n in g.nodes}),
        }

    @app.get("/api/nodes/{node_id}")
    def get_node(node_id: str):
        g: RouteGraph = app.state.graph
        node = next((n for n in g.nodes if n.id == node_id), None)
        if not node:
            raise HTTPException(404, f"Node not found: {node_id}")
        connected = [e for e in g.edges if e.source == node_id or e.target == node_id]
        return {
            "node": node.to_dict(),
            "connected_edges": [e.to_dict() for e in connected],
        }

    @app.post("/api/rescan")
    def rescan():
        nodes, edges = scan_project(root, config)
        new_graph, new_issues = build_graph(nodes, edges)
        app.state.graph = new_graph
        app.state.issues = new_issues
        return {"status": "ok", "nodes": len(new_graph.nodes)}

    # Mount static UI if built
    ui_dist = Path(__file__).parent.parent.parent / "ui" / "dist"
    if ui_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="ui")

    return app
```

- [ ] **Step 4: Add serve command to CLI**

Add to `src/doc_router/cli.py`:

```python
@cli.command()
@click.option("--project", default=None, help="Project root (default: cwd)")
@click.option("--port", default=8030, help="Server port")
def serve(project: str | None, port: int) -> None:
    """Start UI and API server."""
    import uvicorn
    from doc_router.server import create_app

    root = Path(project) if project else Path.cwd()
    app = create_app(project_root=root)
    click.echo(f"Serving doc-router on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_server.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/doc_router/server.py src/doc_router/cli.py tests/test_server.py pyproject.toml
git commit -m "feat(doc-router): FastAPI server with graph API and serve CLI command"
```

---

## Task 11: Frontend — Project Setup + Design System

**Files:**
- Create: `ui/package.json`
- Create: `ui/vite.config.ts`
- Create: `ui/tsconfig.json`
- Create: `ui/tsconfig.app.json`
- Create: `ui/index.html`
- Create: `ui/src/main.tsx`
- Create: `ui/src/App.tsx`
- Create: `ui/src/styles.css` (copy from review-workbench)
- Create: `ui/src/utils/cn.ts` (copy from review-workbench)

- [ ] **Step 1: Create package.json**

```json
{
  "name": "doc-router-ui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@dagrejs/dagre": "^1.1.5",
    "@tanstack/react-query": "^5.94.5",
    "@xyflow/react": "^12.10.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.577.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-resizable-panels": "^4.7.4",
    "tailwind-merge": "^3.5.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.17",
    "@types/react": "^18.3.23",
    "@types/react-dom": "^18.3.7",
    "@vitejs/plugin-react": "^4.4.1",
    "tailwindcss": "^4.0.17",
    "typescript": "^5.8.2",
    "vite": "^5.4.14"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```typescript
// ui/vite.config.ts
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5174,
    proxy: {
      "/api": "http://127.0.0.1:8030",
    },
  },
});
```

- [ ] **Step 3: Create tsconfig files**

```json
// ui/tsconfig.json
{ "files": [], "references": [{ "path": "./tsconfig.app.json" }] }
```

```json
// ui/tsconfig.app.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create index.html**

```html
<!-- ui/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Doc-Router</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Copy styles.css from review-workbench**

Source: `/home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench/src/styles.css`

Copy to `ui/src/styles.css`. No modifications needed — the Terran Command theme is project-agnostic.

- [ ] **Step 6: Copy cn.ts utility**

```typescript
// ui/src/utils/cn.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 7: Create main.tsx and App.tsx**

```typescript
// ui/src/main.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
```

```typescript
// ui/src/App.tsx
export default function App() {
  return (
    <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-on-surface)]">
      <div className="flex items-center justify-center h-screen">
        <h1 className="font-headline text-2xl tracking-widest uppercase text-[var(--color-primary)]">
          Doc-Router
        </h1>
      </div>
    </div>
  );
}
```

- [ ] **Step 8: Create .gitignore**

```
# ui/.gitignore
node_modules/
dist/
```

- [ ] **Step 9: Install and verify**

```bash
cd ui && npm install && npm run dev
```

Expected: Dev server on http://127.0.0.1:5174, showing "DOC-ROUTER" in cyan on dark background.

- [ ] **Step 10: Commit**

```bash
git add ui/
git commit -m "feat(doc-router): frontend scaffold with Terran Command design system"
```

---

## Task 12: Frontend — Atom Components

**Files:**
- Create: `ui/src/components/atoms/Badge.tsx`
- Create: `ui/src/components/atoms/Button.tsx`
- Create: `ui/src/components/atoms/Icon.tsx`
- Create: `ui/src/components/atoms/Spinner.tsx`
- Create: `ui/src/components/atoms/Tag.tsx`

- [ ] **Step 1: Copy atoms from review-workbench**

Copy these files from `/home/jp/phd-workspaces/dev/.worktrees/ui-redesign/apps/review-workbench/src/components/atoms/`:
- `Badge.tsx`
- `Button.tsx`
- `Icon.tsx`
- `Spinner.tsx`
- `Tag.tsx`

Update import paths: change `../../utils/cn` to `@/utils/cn` or relative paths matching the new structure.

- [ ] **Step 2: Verify typecheck**

Run: `cd ui && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add ui/src/components/atoms/
git commit -m "feat(doc-router): copy atom components from review-workbench"
```

---

## Task 13: Frontend — Graph Types + API Client

**Files:**
- Create: `ui/src/types/graph.types.ts`
- Create: `ui/src/api/client.ts`

- [ ] **Step 1: Create TypeScript types mirroring RouteGraph**

```typescript
// ui/src/types/graph.types.ts
export interface RouteNode {
  id: string;
  type: "doc" | "code";
  path: string;
  domain: string;
  stage: string;
  nature: string;
  version: string | null;
  symbol: string | null;
  tags: Record<string, string | null>;
}

export interface RouteEdge {
  source: string;
  target: string;
  type: "implements" | "doc-ref" | "depends_on" | "contract";
}

export interface RouteGraph {
  nodes: RouteNode[];
  edges: RouteEdge[];
}

export interface GraphStats {
  total_nodes: number;
  doc_nodes: number;
  code_nodes: number;
  total_edges: number;
  issues: number;
  domains: string[];
  stages: string[];
}

export interface NodeDetail {
  node: RouteNode;
  connected_edges: RouteEdge[];
}
```

- [ ] **Step 2: Create API client**

```typescript
// ui/src/api/client.ts
import type { GraphStats, NodeDetail, RouteGraph } from "../types/graph.types";

const BASE = "/api";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v) url.searchParams.set(k, v);
    });
  }
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

export const api = {
  getGraph: (filters?: { domain?: string; stage?: string; nature?: string }) =>
    get<RouteGraph>("/graph", filters),
  getStats: () => get<GraphStats>("/stats"),
  getNode: (id: string) => get<NodeDetail>(`/nodes/${encodeURIComponent(id)}`),
  rescan: () => fetch(`${BASE}/rescan`, { method: "POST" }).then((r) => r.json()),
};
```

- [ ] **Step 3: Commit**

```bash
git add ui/src/types/ ui/src/api/
git commit -m "feat(doc-router): TypeScript graph types and API client"
```

---

## Task 14: Frontend — Graph Explorer

**Files:**
- Create: `ui/src/features/graph-explorer/hooks/useRouteGraph.ts`
- Create: `ui/src/features/graph-explorer/lib/colors.ts`
- Create: `ui/src/features/graph-explorer/lib/layout.ts`
- Create: `ui/src/features/graph-explorer/components/DocNode.tsx`
- Create: `ui/src/features/graph-explorer/components/CodeNode.tsx`
- Create: `ui/src/features/graph-explorer/components/RouteEdge.tsx`
- Create: `ui/src/features/graph-explorer/components/FilterBar.tsx`
- Create: `ui/src/features/graph-explorer/components/NodeInspector.tsx`
- Create: `ui/src/features/graph-explorer/components/RouteGraphCanvas.tsx`
- Modify: `ui/src/App.tsx`

- [ ] **Step 1: Create data hook**

```typescript
// ui/src/features/graph-explorer/hooks/useRouteGraph.ts
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../api/client";

interface Filters {
  domain?: string;
  stage?: string;
  nature?: string;
}

export function useRouteGraph(filters: Filters = {}) {
  return useQuery({
    queryKey: ["graph", filters],
    queryFn: () => api.getGraph(filters),
    staleTime: 30_000,
  });
}

export function useGraphStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => api.getStats(),
    staleTime: 30_000,
  });
}
```

- [ ] **Step 2: Create color/layout helpers**

```typescript
// ui/src/features/graph-explorer/lib/colors.ts
const DOMAIN_HUES: Record<string, number> = {
  pipeline: 188,
  ui: 270,
  api: 210,
  core: 168,
  cli: 198,
  data: 36,
  policy: 345,
  practices: 150,
};

export function domainColor(domain: string): string {
  const hue = DOMAIN_HUES[domain] ?? 210;
  return `hsl(${hue} 74% 65%)`;
}

export function domainBg(domain: string): string {
  const hue = DOMAIN_HUES[domain] ?? 210;
  return `hsl(${hue} 40% 15%)`;
}

const NATURE_SHAPES: Record<string, string> = {
  philosophy: "rounded-full",
  implementation: "rounded-md",
  development: "rounded-sm",
  testing: "rounded-none",
};

export function natureShape(nature: string): string {
  return NATURE_SHAPES[nature] ?? "rounded-md";
}
```

```typescript
// ui/src/features/graph-explorer/lib/layout.ts
import Dagre from "@dagrejs/dagre";
import type { RouteNode, RouteEdge } from "../../../types/graph.types";

interface LayoutNode {
  id: string;
  position: { x: number; y: number };
  data: RouteNode;
  type: string;
}

interface LayoutEdge {
  id: string;
  source: string;
  target: string;
  data: RouteEdge;
  type: string;
}

const NODE_WIDTH = 260;
const NODE_HEIGHT = 80;

export function layoutGraph(
  nodes: RouteNode[],
  edges: RouteEdge[],
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", nodesep: 60, ranksep: 120 });

  nodes.forEach((n) => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach((e) => g.setEdge(e.source, e.target));

  Dagre.layout(g);

  const layoutNodes: LayoutNode[] = nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      id: n.id,
      position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
      data: n,
      type: n.type === "doc" ? "docNode" : "codeNode",
    };
  });

  const layoutEdges: LayoutEdge[] = edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    data: e,
    type: "routeEdge",
  }));

  return { nodes: layoutNodes, edges: layoutEdges };
}
```

- [ ] **Step 3: Create custom node components**

```typescript
// ui/src/features/graph-explorer/components/DocNode.tsx
import { Handle, Position } from "@xyflow/react";
import type { RouteNode } from "../../../types/graph.types";
import { domainColor, domainBg } from "../lib/colors";

export function DocNode({ data, selected }: { data: RouteNode; selected: boolean }) {
  const color = domainColor(data.domain);
  const bg = domainBg(data.domain);

  return (
    <div
      className="border px-3 py-2 min-w-[240px]"
      style={{
        borderColor: selected ? "var(--color-primary)" : color,
        backgroundColor: bg,
        borderRadius: "8px",
      }}
    >
      <Handle type="target" position={Position.Left} className="!bg-[var(--color-primary)]" />
      <div className="font-mono text-xs" style={{ color }}>{data.domain}/{data.stage}</div>
      <div className="font-medium text-sm text-[var(--color-on-surface)] truncate">{data.id}</div>
      <div className="text-xs text-[var(--color-on-muted)] truncate">{data.path}</div>
      <Handle type="source" position={Position.Right} className="!bg-[var(--color-primary)]" />
    </div>
  );
}
```

```typescript
// ui/src/features/graph-explorer/components/CodeNode.tsx
import { Handle, Position } from "@xyflow/react";
import type { RouteNode } from "../../../types/graph.types";
import { domainColor, domainBg } from "../lib/colors";

export function CodeNode({ data, selected }: { data: RouteNode; selected: boolean }) {
  const color = domainColor(data.domain);
  const bg = domainBg(data.domain);

  return (
    <div
      className="border-2 border-dashed px-3 py-2 min-w-[240px]"
      style={{
        borderColor: selected ? "var(--color-primary)" : color,
        backgroundColor: bg,
        borderRadius: "4px",
      }}
    >
      <Handle type="target" position={Position.Left} className="!bg-[var(--color-secondary)]" />
      <div className="font-mono text-xs" style={{ color }}>{data.domain}/{data.stage}</div>
      <div className="font-medium text-sm text-[var(--color-on-surface)] truncate">
        {data.symbol ?? data.id}
      </div>
      <div className="text-xs text-[var(--color-on-muted)] truncate">{data.path}</div>
      <Handle type="source" position={Position.Right} className="!bg-[var(--color-secondary)]" />
    </div>
  );
}
```

```typescript
// ui/src/features/graph-explorer/components/RouteEdge.tsx
import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";
import type { RouteEdge as RouteEdgeType } from "../../../types/graph.types";

const EDGE_COLORS: Record<string, string> = {
  implements: "var(--color-primary)",
  "doc-ref": "var(--color-secondary)",
  depends_on: "var(--color-on-muted)",
  contract: "#a855f7",
};

export function RouteEdge(props: EdgeProps & { data: RouteEdgeType }) {
  const [path, labelX, labelY] = getBezierPath(props);
  const color = EDGE_COLORS[props.data.type] ?? "var(--color-outline)";

  return (
    <>
      <BaseEdge
        path={path}
        style={{
          stroke: color,
          strokeWidth: 1.5,
          strokeDasharray: props.data.type === "depends_on" ? "6 3" : undefined,
        }}
      />
      <text
        x={labelX}
        y={labelY - 8}
        className="fill-[var(--color-on-muted)] text-[10px]"
        textAnchor="middle"
      >
        {props.data.type}
      </text>
    </>
  );
}
```

- [ ] **Step 4: Create FilterBar**

```typescript
// ui/src/features/graph-explorer/components/FilterBar.tsx
import { useGraphStats } from "../hooks/useRouteGraph";

interface Props {
  domain: string;
  stage: string;
  nature: string;
  onChange: (filters: { domain: string; stage: string; nature: string }) => void;
}

export function FilterBar({ domain, stage, nature, onChange }: Props) {
  const { data: stats } = useGraphStats();

  return (
    <div className="flex gap-3 items-center px-4 py-2 border-b border-[var(--color-outline)]/30 bg-[var(--color-surface)]">
      <label className="font-mono text-xs text-[var(--color-on-muted)] uppercase">Filters</label>
      <select
        value={domain}
        onChange={(e) => onChange({ domain: e.target.value, stage, nature })}
        className="bg-[var(--color-surface-container)] text-[var(--color-on-surface)] text-xs px-2 py-1 rounded border border-[var(--color-outline)]/30"
      >
        <option value="">All domains</option>
        {stats?.domains.map((d) => <option key={d} value={d}>{d}</option>)}
      </select>
      <select
        value={stage}
        onChange={(e) => onChange({ domain, stage: e.target.value, nature })}
        className="bg-[var(--color-surface-container)] text-[var(--color-on-surface)] text-xs px-2 py-1 rounded border border-[var(--color-outline)]/30"
      >
        <option value="">All stages</option>
        {stats?.stages.map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
      {stats && (
        <span className="ml-auto font-mono text-xs text-[var(--color-on-muted)]">
          {stats.total_nodes} nodes / {stats.total_edges} edges
        </span>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Create NodeInspector**

```typescript
// ui/src/features/graph-explorer/components/NodeInspector.tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../api/client";
import { Badge } from "../../../components/atoms/Badge";

interface Props {
  nodeId: string | null;
  onClose: () => void;
}

export function NodeInspector({ nodeId, onClose }: Props) {
  const { data } = useQuery({
    queryKey: ["node", nodeId],
    queryFn: () => api.getNode(nodeId!),
    enabled: !!nodeId,
  });

  if (!nodeId || !data) return null;
  const { node, connected_edges } = data;

  return (
    <div className="w-80 border-l border-[var(--color-outline)]/30 bg-[var(--color-surface)] p-4 overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-headline text-sm uppercase tracking-wider text-[var(--color-primary)]">
          Inspector
        </h3>
        <button onClick={onClose} className="text-[var(--color-on-muted)] hover:text-[var(--color-on-surface)]">
          &times;
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <div className="font-mono text-xs text-[var(--color-on-muted)]">ID</div>
          <div className="text-sm">{node.id}</div>
        </div>
        <div className="flex gap-2">
          <Badge variant="primary">{node.domain}</Badge>
          <Badge variant="secondary">{node.stage}</Badge>
          <Badge variant="muted">{node.nature}</Badge>
        </div>
        <div>
          <div className="font-mono text-xs text-[var(--color-on-muted)]">Path</div>
          <div className="text-sm font-mono">{node.path}</div>
        </div>
        {node.symbol && (
          <div>
            <div className="font-mono text-xs text-[var(--color-on-muted)]">Symbol</div>
            <div className="text-sm font-mono">{node.symbol}</div>
          </div>
        )}
        {node.version && (
          <div>
            <div className="font-mono text-xs text-[var(--color-on-muted)]">Version</div>
            <div className="text-sm">{node.version}</div>
          </div>
        )}
        {Object.keys(node.tags).length > 0 && (
          <div>
            <div className="font-mono text-xs text-[var(--color-on-muted)] mb-1">Tags</div>
            {Object.entries(node.tags).map(([k, v]) =>
              v ? <div key={k} className="text-xs font-mono">{k}: {v}</div> : null
            )}
          </div>
        )}
        <div>
          <div className="font-mono text-xs text-[var(--color-on-muted)] mb-1">
            Edges ({connected_edges.length})
          </div>
          {connected_edges.map((e, i) => (
            <div key={i} className="text-xs font-mono">
              {e.source === node.id ? `→ ${e.target}` : `← ${e.source}`}
              <span className="text-[var(--color-on-muted)]"> ({e.type})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Create RouteGraphCanvas**

```typescript
// ui/src/features/graph-explorer/components/RouteGraphCanvas.tsx
import {
  ReactFlow,
  Background,
  Controls,
  type OnNodeClick,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo, useState } from "react";
import { useRouteGraph } from "../hooks/useRouteGraph";
import { layoutGraph } from "../lib/layout";
import { DocNode } from "./DocNode";
import { CodeNode } from "./CodeNode";
import { RouteEdge } from "./RouteEdge";
import { FilterBar } from "./FilterBar";
import { NodeInspector } from "./NodeInspector";
import { Spinner } from "../../../components/atoms/Spinner";

const nodeTypes = { docNode: DocNode, codeNode: CodeNode };
const edgeTypes = { routeEdge: RouteEdge };

export function RouteGraphCanvas() {
  const [filters, setFilters] = useState({ domain: "", stage: "", nature: "" });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const queryFilters = {
    domain: filters.domain || undefined,
    stage: filters.stage || undefined,
    nature: filters.nature || undefined,
  };
  const { data: graph, isLoading } = useRouteGraph(queryFilters);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };
    return layoutGraph(graph.nodes, graph.edges);
  }, [graph]);

  const handleNodeClick: OnNodeClick = (_, node) => {
    setSelectedNode(node.id);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="md" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <FilterBar {...filters} onChange={setFilters} />
      <div className="flex flex-1 min-h-0">
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodeClick={handleNodeClick}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="var(--color-outline)" gap={20} size={1} />
            <Controls />
          </ReactFlow>
        </div>
        <NodeInspector nodeId={selectedNode} onClose={() => setSelectedNode(null)} />
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Update App.tsx**

```typescript
// ui/src/App.tsx
import { RouteGraphCanvas } from "./features/graph-explorer/components/RouteGraphCanvas";

export default function App() {
  return (
    <div className="h-screen flex flex-col bg-[var(--color-background)] text-[var(--color-on-surface)]">
      <header className="flex items-center gap-3 px-4 py-2 border-b border-[var(--color-outline)]/30 bg-[var(--color-surface)]">
        <h1 className="font-headline text-sm tracking-widest uppercase text-[var(--color-primary)]">
          Doc-Router
        </h1>
      </header>
      <main className="flex-1 min-h-0">
        <RouteGraphCanvas />
      </main>
    </div>
  );
}
```

- [ ] **Step 8: Verify it works end-to-end**

Terminal 1: `doc-router serve --project . --port 8030`
Terminal 2: `cd ui && npm run dev`

Open http://127.0.0.1:5174 — should show the graph explorer with nodes from the project.

- [ ] **Step 9: Commit**

```bash
git add ui/src/features/ ui/src/App.tsx
git commit -m "feat(doc-router): interactive graph explorer with React Flow"
```

---

## Task 15: Create PhD 2.0 Project Config

**Files:**
- Create: `doc-router.yml` (project root)

- [ ] **Step 1: Create config for this project**

```yaml
# doc-router.yml
project: phd-2.0
domains: [ui, api, pipeline, core, cli, data, policy, practices]
stages: [scrape, translate, extract, match, strategy, drafting, render, package]
natures: [philosophy, implementation, development, testing, design, migration]
doc_paths:
  central: docs/
  seed: docs/seed/
source_paths:
  - src/
  - apps/review-workbench/src/
```

- [ ] **Step 2: Smoke test against the project**

Run: `doc-router scan --project .`
Expected: Shows count of any already-tagged docs (the seed docs don't have frontmatter tags yet, so expect 0 or low numbers). No crashes.

Run: `doc-router lint --project .`
Expected: Clean pass (no nodes = no violations)

- [ ] **Step 3: Commit**

```bash
git add doc-router.yml
git commit -m "feat(doc-router): add PhD 2.0 project config"
```

---

## Task 16: Tag First Seed Documents

**Files:**
- Modify: `docs/doc-router-design.md` (add frontmatter)
- Modify: `docs/seed/product/03_methodology.md` (add frontmatter)
- Modify: `docs/seed/product/04_pipeline_stages_phd2.md` (add frontmatter)

- [ ] **Step 1: Tag doc-router-design.md**

Add YAML frontmatter to the top of the file:

```markdown
---
id: practices-doc-router-design
domain: practices
stage: global
nature: design
version: 2026-03-22
---
```

- [ ] **Step 2: Tag methodology doc**

```markdown
---
id: policy-methodology
domain: policy
stage: global
nature: philosophy
version: 2026-03-22
---
```

- [ ] **Step 3: Tag pipeline stages doc**

```markdown
---
id: pipeline-stages-overview
domain: pipeline
stage: global
nature: philosophy
depends_on:
  - policy-methodology
version: 2026-03-22
---
```

- [ ] **Step 4: Verify scan finds them**

Run: `doc-router scan --project .`
Expected: `3 nodes (3 docs, 0 code), 1 edges`

Run: `doc-router graph --project .`
Expected: Lists all 3 nodes and the depends_on edge.

- [ ] **Step 5: Commit**

```bash
git add docs/doc-router-design.md docs/seed/product/03_methodology.md docs/seed/product/04_pipeline_stages_phd2.md
git commit -m "docs: tag first seed documents with doc-router frontmatter"
```

---

## Completion Criteria

Phase 1 is done when:

- [ ] `doc-router scan` parses markdown frontmatter and Python docstrings
- [ ] `doc-router lint` validates tags against `doc-router.yml` vocabulary
- [ ] `doc-router graph` prints or exports the route graph as JSON
- [ ] `doc-router serve` starts a FastAPI server with graph API
- [ ] Graph Explorer UI renders nodes, edges, filters, and node inspector
- [ ] At least 3 seed documents are tagged and scannable
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] UI typechecks: `cd ui && npx tsc --noEmit`
