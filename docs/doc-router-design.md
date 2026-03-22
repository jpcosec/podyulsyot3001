# Doc-Router: Documentation-Driven Development Framework

**Date:** 2026-03-22
**Status:** Design
**Type:** Reusable CLI framework

---

## Overview

Doc-Router is a lightweight CLI framework that treats project documentation as a navigable, queryable graph. It scans tagged docs and code, detects drift between them, generates precise task packets for AI agents, and provides a UI for inspecting, editing, and correcting plans.

It does NOT execute code, call LLMs, or manage git. It produces the instructions — you choose how to run them.

### Core Value

A tool that always knows where everything is, how it connects, and can generate precise instructions from that knowledge.

### Integration Model

- **CLI** — `pip install doc-router`, run commands
- **UI** — `doc-router serve` starts a local web app (inspector + editor + graph + task generator)
- **MCP** — The UI backend doubles as an MCP server (free from the API)
- **Skills** — Fallback if no UI: wrap CLI commands in agent skills

---

## 1. Tag Schema

The foundation. Developers annotate code and docs so the framework can build the graph.

### 1.1 In Docs (YAML Frontmatter)

```markdown
---
id: pipeline-match-design
domain: pipeline
stage: match
nature: philosophy
implements:
  - src/nodes/match/logic.py
  - src/nodes/match/contract.py
depends_on:
  - pipeline-extract-design
version: 2026-03-22
---
```

### 1.2 In Code

**Python** — structured docstrings:

```python
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
```

**TypeScript** — JSDoc:

```typescript
/**
 * @doc-id ui-match-view
 * @domain ui
 * @stage match
 * @nature implementation
 * @doc-ref pipeline-match-design
 */
```

### 1.3 Tag Rules

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Globally unique, human-readable identifier |
| `domain` | Yes | Which part of the system (from project vocabulary) |
| `stage` | No | Which pipeline step (from project vocabulary). Defaults to `global` if omitted |
| `nature` | Yes | Document type (from project vocabulary, e.g. `philosophy`, `implementation`, `development`, `testing`) |
| `implements` | No | Doc → code links (list of file paths or `path::Symbol`) |
| `doc-ref` | No | Code → doc links (doc `id` references) |
| `depends_on` | No | Doc → doc dependency edges |
| `contract` | No | Links to schema/contract definitions |
| `hitl-gate` | No | Names the HITL review point, if any |
| `version` | Yes (docs) | Last-verified date. See drift detection rules below |

### 1.4 Project Config

```yaml
# doc-router.yml (project root)
project: my-project
domains: [ui, api, pipeline, core, cli, data, policy]
stages: [scrape, translate, extract, match, strategy, drafting, render, package]
natures: [philosophy, implementation, development, testing]
doc_paths:
  central: docs/
  plans: plan/
templates:
  docs: templates/docs/
  code: templates/code/
```

The vocabulary is per-project. Doc-Router validates tags against this config — unknown domains or stages are lint errors.

---

## 2. Core Engine

Five components. Each is a vertical slice that delivers value independently.

### 2.1 Scanner & Graph Builder

Two-step pipeline: scan (parse tags) → build (resolve references).

- **Input:** Project root + `doc-router.yml`
- **Scan paths:** All directories listed in `doc_paths` for docs; all `src/` (or configured source roots) for code docstrings
- **Output:** `RouteGraph` — the core data model (see below)

**Scanning:**
- Parses YAML frontmatter from `.md` files
- Parses `:doc-*:` from Python docstrings, `@doc-*` from JSDoc
- Validates tags against vocabulary in `doc-router.yml`
- Produces a flat list of `TaggedEntity` records

**Building:**
- Resolves cross-references (`implements`, `doc-ref`, `depends_on`) into edges
- Detects broken links (tag points to nonexistent file/symbol)
- Computes connected components (isolated nodes = potential gaps)
- Caches result at `.doc-router/cache.json`

**Cache invalidation:** The cache stores a hash of each scanned file. On subsequent runs, only files with changed hashes are re-scanned. `doc-router scan --force` rebuilds from scratch.

#### RouteGraph Schema

```json
{
  "nodes": [
    {
      "id": "pipeline-match-design",
      "type": "doc",
      "path": "docs/product/match.md",
      "domain": "pipeline",
      "stage": "match",
      "nature": "philosophy",
      "version": "2026-03-22",
      "symbol": null,
      "tags": { "hitl_gate": null, "contract": null }
    },
    {
      "id": "pipeline-match-impl",
      "type": "code",
      "path": "src/nodes/match/logic.py",
      "domain": "pipeline",
      "stage": "match",
      "nature": "implementation",
      "version": null,
      "symbol": "MatchLogic",
      "tags": { "hitl_gate": "review_match", "contract": "src/nodes/match/contract.py::MatchInput" }
    }
  ],
  "edges": [
    {
      "source": "pipeline-match-design",
      "target": "pipeline-match-impl",
      "type": "implements"
    },
    {
      "source": "pipeline-match-impl",
      "target": "pipeline-match-design",
      "type": "doc-ref"
    }
  ]
}
```

**Node types:** `doc` (markdown file) or `code` (tagged symbol within a source file). A single file can produce multiple `code` nodes if it contains multiple tagged symbols.

**Edge types:** `implements` (doc → code), `doc-ref` (code → doc), `depends_on` (doc → doc), `contract` (any → schema definition).

### 2.2 Drift Detector

Compares tag state against filesystem state.

| Check | Severity | Description |
|-------|----------|-------------|
| **Staleness** | Warning | Content hash of linked code changed since last `doc-router verify` |
| **Broken links** | Error | `implements` or `doc-ref` target doesn't exist |
| **Orphans** | Info | Code with no tags, docs with no `implements` targets |
| **Vocabulary violations** | Error | Tags using domains/stages not in `doc-router.yml` |
| **Asymmetric links** | Warning | Doc declares `implements: X` but X has no `doc-ref` back (or vice versa) |

**Staleness model:** Uses content hashing, not mtime. The scanner stores a hash of each file's tagged symbols. `doc-router verify` marks a doc-to-code link as "verified" by recording the current hash. When the code's hash changes, the link becomes stale. This avoids false positives from formatting-only changes (the hash covers the symbol's signature and body, not whitespace).

**Asymmetric links:** Both `implements` and `doc-ref` are optional individually — you can link from either direction. But the drift detector warns when a link exists in only one direction, since bidirectional links are more robust. This is a warning, not an error — single-direction links are valid for lightweight tagging.

Output: drift report (JSON + human-readable) with severity levels.

### 2.3 Template Engine

Two functions:

**Scaffolding** — Generate new docs/code from templates:

```bash
doc-router new doc --domain pipeline --stage match --nature philosophy
doc-router new code --domain pipeline --stage match --lang python
```

Templates are Jinja2 in the project's `templates/` dir. Auto-populate tags from arguments.

**Runbook generation** — Produce "how to" instructions from tagged code:

```bash
doc-router runbook --domain api --stage match
```

Follows the graph from the target node, collects tagged content and assembles a runbook. The runbook extracts:
- CLI commands from docs tagged with `nature: development`
- API endpoints from docs tagged with `nature: implementation` in the `api` domain
- Config references from `doc-router.yml` and linked contracts
- Related docs from `depends_on` edges

This is what makes "you can always get the code and docs for things" work. The content comes from the tagged docs themselves — no new tag fields needed.

### 2.4 Packet Compiler

The prompt/task generator. Given a task description and explicit coordinates, resolves minimal context.

```bash
# Explicit routing (preferred — deterministic)
doc-router packet --domain pipeline --stage match --task "add confidence field" --type implement

# Keyword fallback (returns candidates for user to select)
doc-router packet --task "add confidence field to match output" --type implement
```

**Resolution strategy:** The compiler does NOT attempt NLP on the task description. Instead:

1. If `--domain` and `--stage` are provided → direct graph lookup (deterministic)
2. If omitted → keyword match against node IDs, tags, and file paths → return ranked candidates → user selects
3. Once the target nodes are identified → follow edges to include contracts, dependencies, HITL gates
4. Apply task-type template (`implement`, `test`, `fix`, `review`)

**Output** — structured packet:

- **Intent:** What to do (the task description)
- **Context:** Relevant files with content (docs) or references (code)
- **Constraints:** Writable paths (derived from `implements` targets) vs read-only (everything else)
- **Acceptance criteria:** How to verify success (from linked test docs and contract schemas)
- **Examples:** Similar past corrections (if correction history exists)

The packet is a markdown file — paste into any LLM, use as a skill prompt, or serve via MCP.

---

## 3. CLI Interface

```
doc-router init                              # Create doc-router.yml + templates/
doc-router scan [--force]                    # Build graph, report stats
doc-router lint                              # Validate tags, check vocabulary
doc-router drift                             # Run drift detection
doc-router verify [--domain X] [--stage Y]   # Mark doc-code links as verified (updates hashes)
doc-router graph [--domain X] [--stage Y]    # Print graph (text) or export JSON
doc-router check                             # Combined lint + drift (single health check)
doc-router new doc|code [--domain] [--stage] # Scaffold from template
doc-router runbook --domain X --stage Y      # Generate runbook
doc-router packet --task "..." --type T      # Compile task packet
  [--domain X] [--stage Y]                   # Optional explicit routing
doc-router serve                             # Start UI server (+ MCP after Phase 6)
```

All commands support `--json` for programmatic use.

---

## 4. UI Architecture

Single local web app served by `doc-router serve`. Reuses PhD graph editor (React Flow) and workbench components (CodeMirror, Tailwind atoms).

### 4.1 Graph Explorer (Phase 1)

- Interactive graph of all tagged entities
- Filter by domain, stage, nature
- Click node → tags, content preview, linked nodes
- Color-coded by domain, shape-coded by nature
- Edge types visually distinct (implements, depends_on, contract)

### 4.2 Drift Dashboard (Phase 2)

- Health overview: green/yellow/red per domain and stage
- List of drift issues with severity
- Click issue → navigate to file in editor
- Historical trend stored in `.doc-router/history/`

### 4.3 Document & Code Editor (Phase 3)

- Split pane: rendered preview + source editor
- Markdown editor with frontmatter-aware editing
- Syntax-highlighted code view with tag regions highlighted
- Template insertion commands
- Save writes back to filesystem

### 4.4 Task Generator & Correction View (Phase 4-5)

- Select task type (implement, test, fix, review)
- Describe task, provide domain/stage coordinates
- See resolved context graph (which nodes selected, why)
- Edit/correct packet before exporting
- Correction history: track changes to generated packets, feed back into template refinement

#### Correction History Model

Corrections are stored in `.doc-router/corrections/`:

```json
{
  "id": "corr-2026-03-22-001",
  "timestamp": "2026-03-22T14:30:00Z",
  "packet_id": "implement-pipeline-match-001",
  "domain": "pipeline",
  "stage": "match",
  "type": "implement",
  "changes": [
    {
      "field": "context",
      "action": "added",
      "value": "src/nodes/match/contract.py",
      "reason": "Compiler missed the contract file"
    },
    {
      "field": "constraints",
      "action": "removed",
      "value": "src/core/graph/state.py",
      "reason": "This file does need modification for the new field"
    }
  ]
}
```

Over time, corrections reveal patterns: "the compiler always misses contract files for pipeline tasks" → adjust the edge-following rules or templates.

### 4.5 Tech Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Frontend | React + Tailwind | Reuse PhD workbench atoms/molecules |
| Graph | React Flow | Reuse PhD graph editor |
| Editor | CodeMirror | Already in PhD workbench |
| Backend | FastAPI | Serves API + static UI + MCP |
| Data | Filesystem | Scanned graph cached as `.doc-router/cache.json` |

---

## 5. MCP Server

`doc-router serve` exposes the backend as MCP tools:

| Tool | Description |
|------|-------------|
| `query_route` | Find docs/code by domain, stage, nature |
| `check_drift` | Run drift detection, return report |
| `get_context` | Given a file/symbol, return its full context graph |
| `generate_packet` | Compile a task packet from description |
| `get_runbook` | Generate runbook for a domain/stage |
| `list_templates` | Available doc/code templates |
| `scaffold` | Create new doc/code from template |

MCP resources expose the graph itself — clients can browse nodes and edges directly.

---

## 6. `.doc-router/` Directory

Generated data stored locally:

| Path | Purpose | Git |
|------|---------|-----|
| `.doc-router/cache.json` | Scanned graph cache | `.gitignore` |
| `.doc-router/hashes.json` | Content hashes for drift detection | Commit (shared state) |
| `.doc-router/corrections/` | Correction history | Commit (team learning) |
| `.doc-router/history/` | Drift report snapshots over time | Optional |

---

## 7. Development Phases

Each phase delivers a working vertical slice (schema → engine → CLI → API → UI):

| Phase | Engine | CLI | UI | Delivers |
|-------|--------|-----|-----|----------|
| **1** | Scanner + Graph Builder | `init`, `scan`, `lint`, `graph`, `serve` | Graph Explorer | See your project as a navigable network |
| **2** | Drift Detector | `drift`, `verify` | Drift Dashboard | Know what's broken or stale |
| **3** | Template Engine | `new`, `runbook` | Document Editor | Create and edit with templates |
| **4** | Packet Compiler | `packet` | Task Generator | Produce precise agent instructions |
| **5** | Correction Tracker | — | Correction View | Review and improve over time |
| **6** | MCP Protocol | — | — | Add MCP protocol to existing `serve` |

`doc-router serve` ships in Phase 1 (for the UI). Phase 6 adds MCP protocol support to the same server — no new command needed.

---

## 8. Boundaries

What Doc-Router does NOT do:

- **No code execution** — Does not compile, run tests, or call LLMs
- **No git management** — No commit, push, or branch operations
- **No real-time collaboration** — Single user, local tool
- **No model integration** — Generates prompts/packets; you dispatch them
- **No runtime enforcement** — Advisory + linting, not a gatekeeper
- **No project structure requirements** — Adapts via `doc-router.yml`

---

## 9. Relation to Existing Work

| Asset | How Doc-Router Uses It |
|-------|----------------------|
| PhD Graph Editor (React Flow) | Reuse as the graph explorer view |
| PhD Workbench atoms/molecules | Reuse UI components (Button, Badge, SplitPane, etc.) |
| PhD CodeMirror integration | Reuse for the document/code editor |
| PhD seed docs (routing matrix) | Migration target: replace the 79-row manual matrix with distributed tags |
| PhD `doc-router.yml` | First consumer project config |
