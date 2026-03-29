# Pipeline Unification Design

**Date:** 2026-03-29
**Status:** Draft
**Scope:** Unify all modules under a single orchestrated pipeline with shared IO, CLI, LangGraph graph, and Textual TUI.

---

## 1. Problem Statement

The codebase has working modules (`scraper`, `translator`, `match_skill`, `generate_documents`, `render`) that were built independently. Each has its own storage pattern, its own CLI, its own way of reading the previous step's output. There is no single entry point that runs the pipeline end-to-end. The issues tracked in `future_docs/issues/` (orchestration, review_ui_wiring, testing_and_data_management) are all symptoms of the same root cause: the modules were never designed to compose.

**What this design solves:**

- No unified IO layer — each module invents its own path conventions and storage code
- No end-to-end pipeline — users chain CLI commands manually
- No shared review pattern — match_skill has TUI review, other nodes have nothing
- No compatibility checks between step outputs and step inputs
- No way to test the full pipeline as a single unit
- Scraper is under `src/scraper/` but is deterministic tooling, not an LLM skill

---

## 2. Design Principles

These are the rules this design follows. They come from the user's constraints and the project's existing standards.

1. **State is managed by LangGraph.** The graph checkpoint is the single source of truth for control flow. Node outputs persist to disk — state carries refs, not payloads.

2. **LangGraph-native first.** Use native LangGraph patterns (StateGraph, Command routing, interrupt_before, checkpointing) wherever possible. Do not build custom orchestration when LangGraph has a native answer.

3. **LangChain-native for LLM boundaries.** LLM calls use `ChatPromptTemplate` + `with_structured_output()`. No custom LLM wrappers.

4. **Tools are tools, skills are skills.** Deterministic modules (scraper, translator, render) live under `src/tools/`. LLM-based modules (match_skill, generate_documents, future extract_understand) live under `src/skills/`. This is the existing `tools/` convention extended.

5. **Each module has a standalone entrypoint.** A module can be invoked independently with clear typed inputs and outputs. The CLI, LangGraph graph, and TUI are consumers of these entrypoints — not replacements.

6. **Tested libraries over custom code.** Use LangGraph checkpointing (SqliteSaver), Pydantic for contracts, Textual for TUI. Don't reinvent.

7. **Clean code, not purist code.** Inline documentation where logic is non-obvious. No premature abstractions. No shared utils folder yet — extract later when patterns repeat.

8. **Standards compliance.** All new code follows `docs/standards/docs/` (README structure, LogTag usage, pydoc conventions) and `docs/standards/code/` (existing code standards).

---

## 3. Architecture Overview

### 3.1 Layer Model

```
Layer 4:  Textual TUI           ─── interactive operator interface
Layer 3:  LangGraph Graph       ─── orchestration, checkpointing, HITL breakpoints
Layer 2:  Unified CLI            ─── per-module commands + pipeline runner
Layer 1:  Module Entrypoints    ─── each module's run() with typed IO
Layer 0:  Core IO               ─── WorkspaceManager, ArtifactReader/Writer, Provenance
```

Each layer depends only on the layer below it. The TUI never calls disk IO directly — it goes through the graph. The CLI never constructs storage objects — it calls module entrypoints. Module entrypoints never invent path conventions — they use Core IO.

### 3.2 Module Classification

| Module | Type | Location | LangGraph Role |
|--------|------|----------|----------------|
| scraper | deterministic tool | `src/tools/scraper/` | tool-node (thin wrapper) |
| translator | deterministic tool | `src/tools/translator/` | tool-node (thin wrapper) |
| render | deterministic tool | `src/tools/render/` | tool-node (thin wrapper) |
| match_skill | LLM skill | `src/skills/match_skill/` | native subgraph with HITL breakpoint |
| generate_documents | LLM skill | `src/skills/generate_documents/` | native node with structured output |
| extract_understand | LLM skill (future) | `src/skills/extract_understand/` | native node (deferred — deterministic bridge for now) |

**Why this split:** Tools are stateless transformers — give them input, get output, no LLM reasoning. Skills involve LLM calls, structured output, and may have review gates. The `src/tools/` folder already exists and contains translator and render. Moving scraper there makes the taxonomy honest.

### 3.3 Directory Structure (Target)

```
src/
  core/                          # Layer 0: shared IO and contracts
    io/
      workspace_manager.py       # path resolution, traversal prevention
      artifact_reader.py         # read JSON/text from workspace
      artifact_writer.py         # atomic write JSON/text to workspace
      provenance_service.py      # SHA256 hashing, integrity
    round_manager.py             # immutable review round storage
    state.py                     # GraphState TypedDict, RunStatus, ErrorContext
    contracts.py                 # shared Pydantic models (ReviewSurface, ReviewPayload, etc.)

  tools/                         # Layer 1: deterministic modules
    scraper/                     # moved from src/scraper/
      (existing files unchanged)
    translator/                  # already here
      (existing files unchanged)
    render/                      # already here
      (existing files unchanged)

  skills/                        # Layer 1: LLM-based modules
    match_skill/                 # moved from src/match_skill/
      contracts.py
      graph.py                   # subgraph definition
      prompt.py
      storage.py                 # delegates to core/io
    generate_documents/          # moved from src/generate_documents/
      contracts.py
      graph.py
      prompt.py
      storage.py                 # delegates to core/io
      review.py
      templates/

  graph.py                       # Layer 3: top-level pipeline graph
  cli/                           # Layer 2: unified CLI
    __init__.py
    main.py                      # click/argparse dispatcher
    run_pipeline.py              # full pipeline runner
    run_match_skill.py           # standalone match skill runner
    review_tui.py                # TUI launcher

  ui/                            # Layer 4: Textual TUI
    app.py
    bus.py
    screens/
    widgets/

  shared/                        # cross-cutting (LogTag, etc.)
    log_tags.py
```

---

## 4. Layer 0: Core IO

### 4.1 Decision: Adopt the dev branch IO layer

The dev branch has a mature IO layer (`WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService`, `RoundManager`) that solves exactly the problems we have. Rather than inventing a new one, we adopt it with minor adaptations.

**What we adopt:**
- `WorkspaceManager` — path resolution with directory traversal prevention. Hierarchical: `{root}/{source}/{job_id}/nodes/{node_name}/{stage}/{filename}`.
- `ArtifactReader` / `ArtifactWriter` — UTF-8 text and JSON IO with atomic writes (temp file + fsync + rename).
- `ProvenanceService` — deterministic SHA256 hashing for integrity checking.
- `RoundManager` — immutable round-based review artifact storage.

**What we change:**
- The dev branch IO layer lives at `src/core/io/`. We keep this location.
- The existing `MatchArtifactStore` and `DocumentArtifactStore` become thin facades over `ArtifactWriter` + `WorkspaceManager`. They keep their module-specific convenience methods but delegate actual IO to core.
- The `output/` directory convention (used by current match_skill) is replaced by `data/jobs/` (the dev branch convention). This is more appropriate — `output/` is ambiguous; `data/jobs/` is semantically clear.

**Why not build a new one:** The dev branch layer is tested, handles edge cases (atomic writes, traversal prevention, provenance), and follows the exact pattern we need. Building a new one would duplicate effort and risk missing durability guarantees.

### 4.2 Data Plane Layout

All pipeline artifacts live under a single workspace root:

```
data/jobs/{source}/{job_id}/
  nodes/
    scrape/
      proposed/
        state.json               # JobPosting model dump
        content.md               # raw markdown
        scrape_meta.json         # extraction metadata
    translate/
      proposed/
        state.json               # translated JobPosting
        content_en.md
    extract_understand/
      proposed/
        state.json               # JobUnderstandingExtract (future)
                                 # For now: deterministic RequirementInput list
    match/
      approved/
        state.json               # MatchEnvelope
      review/
        current.json             # ReviewSurface
        decision.json            # latest DecisionEnvelope
        rounds/
          round_001/
            proposal.json
            decision.json
            feedback.json
    generate_documents/
      proposed/
        deltas.json              # DocumentDeltas
        cv.md
        cover_letter.md
        email_body.txt
      review/
        assist.json              # deterministic review indicators
    render/
      proposed/
        cv.pdf
        cover_letter.pdf
    package/
      final/
        manifest.json
        cv.pdf
        cover_letter.pdf
        email_body.txt
```

**Stage convention:** `proposed/` is the working output of a node. `approved/` is the output after human review. Nodes without review gates write to `proposed/` only. Nodes with review gates promote `proposed/` → `approved/` on approval.

### 4.3 GraphState

Adopted from the dev branch with simplifications:

```python
class GraphState(TypedDict, total=False):
    # Identity (required at start)
    source: str
    job_id: str
    run_id: str

    # Routing
    current_node: str
    status: RunStatus                    # "running" | "pending_review" | "failed" | "completed"
    review_decision: ReviewDecision      # "approve" | "request_regeneration" | "reject"
    pending_gate: str                    # which review node is waiting

    # Inputs (loaded once at start)
    source_url: str                      # for scraper
    profile_evidence: list[dict]         # from reference_data

    # Artifact refs (lightweight pointers — no payloads in state)
    artifact_refs: dict[str, str]

    # Error tracking
    error_state: ErrorContext
```

**Key difference from current match_skill:** The current `MatchSkillState` carries full payloads (`requirements`, `match_result`, `effective_profile_evidence`). The unified state carries only refs. Each node reads what it needs from disk via `ArtifactReader`.

**Why refs-only:** Smaller checkpoints, clearer node boundaries, and nodes can be tested independently by providing fixture files.

---

## 5. Layer 1: Module Entrypoints

### 5.1 Tool Node Pattern

Every tool module exposes a `run()` function with this shape:

```python
def run(
    *,
    source: str,
    job_id: str,
    workspace: WorkspaceManager,
    # tool-specific inputs
    **kwargs,
) -> dict[str, str]:
    """Run the tool. Returns artifact_refs dict."""
```

The function:
1. Reads its inputs (from disk via workspace, or from kwargs)
2. Does its work (scrape, translate, render)
3. Writes its outputs to the workspace
4. Returns a dict of artifact refs (paths to what it wrote)

**The LangGraph wrapper** for each tool is a thin function:

```python
def scrape_node(state: GraphState) -> dict:
    refs = scraper.run(
        source=state["source"],
        job_id=state["job_id"],
        workspace=workspace,
        source_url=state["source_url"],
    )
    return {"artifact_refs": {**state.get("artifact_refs", {}), **refs}, "current_node": "scrape"}
```

This is intentionally boring. The wrapper does nothing but bridge state → kwargs → refs.

### 5.2 Skill Node Pattern

LLM skills are LangGraph subgraphs or nodes that use native patterns:

```python
def build_match_skill_subgraph(
    *,
    chain: Runnable | None = None,
    workspace: WorkspaceManager,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledGraph:
    """Build the match skill subgraph with HITL breakpoint."""
```

Skills:
1. Read inputs from disk (via workspace + artifact_refs from state)
2. Invoke LLM via `ChatPromptTemplate` + `with_structured_output()`
3. Write outputs to disk
4. Return updated artifact_refs
5. May include `interrupt_before` breakpoints for HITL review

### 5.3 The Extract Bridge (Temporary)

Until `extract_understand` is ported as an LLM skill, a deterministic bridge transforms scraper output into match_skill input:

```python
def bridge_extract(
    *,
    source: str,
    job_id: str,
    workspace: WorkspaceManager,
) -> dict[str, str]:
    """Deterministic bridge: JobPosting.requirements → RequirementInput list."""
```

Logic:
1. Read `nodes/scrape/proposed/state.json` (or `translate/proposed/` if translated)
2. For each `requirements` string, assign an ID (`REQ_001`, `REQ_002`, ...)
3. Write `nodes/extract_understand/proposed/state.json` with the `RequirementInput` list
4. Return artifact refs

This is explicitly temporary. When `extract_understand` is ported from the dev branch, this bridge is replaced by the LLM node. The contract (output schema) stays the same — downstream nodes don't change.

### 5.4 Profile Evidence Loading

Profile evidence is loaded from `/home/jp/phd-workspaces/legacy/data/reference_data/` at pipeline start. It's injected into state as `profile_evidence` and does not change during the run (patch evidence from review rounds is handled separately by the match skill's internal round management).

---

## 6. Layer 2: Unified CLI

### 6.1 Structure

One CLI entry point with subcommands:

```
python -m src.cli.main <command> [options]

Commands:
  pipeline    Run the full pipeline (scrape → ... → package)
  scrape      Run scraper only
  translate   Run translator only
  match       Run match skill only
  generate    Run document generation only
  render      Run render only
  review      Launch TUI for HITL review
```

Each subcommand maps to a module entrypoint. The `pipeline` command wires them together via the LangGraph graph.

### 6.2 Pipeline Command

```bash
python -m src.cli.main pipeline \
  --source stepstone \
  --job-id 12345 \
  --source-url "https://..." \
  --profile-evidence /path/to/evidence.json
```

Resume after HITL review:

```bash
python -m src.cli.main pipeline \
  --source stepstone \
  --job-id 12345 \
  --resume
```

The CLI:
1. Constructs `WorkspaceManager`, `SqliteSaver`, profile evidence
2. Builds the top-level graph (see Layer 3)
3. Invokes or resumes the graph
4. Prints a JSON summary to stdout

### 6.3 Standalone Commands

Each module can be run independently for debugging or partial pipeline execution:

```bash
# Just scrape
python -m src.cli.main scrape --source stepstone --limit 5

# Just match (assumes scrape+translate already ran)
python -m src.cli.main match --source stepstone --job-id 12345 --profile-evidence evidence.json

# Just render (assumes generate_documents already ran)
python -m src.cli.main render --source stepstone --job-id 12345 --document cv --language en
```

---

## 7. Layer 3: LangGraph Pipeline Graph

### 7.1 Graph Topology

```
scrape_node
    ↓
translate_node
    ↓
extract_bridge_node              (deterministic, temporary)
    ↓
match_skill_subgraph             (LLM + HITL breakpoint)
    ↓  (on approve)
generate_documents_node          (LLM + deterministic review)
    ↓
render_node
    ↓
package_node
    ↓
__end__
```

Review gates:
- `match_skill_subgraph` has `interrupt_before` at its internal `human_review_node`
- `generate_documents` can optionally have a review gate (future — the deterministic indicators already exist)

Routing after match review:
- `approve` → `generate_documents_node`
- `request_regeneration` → loops inside `match_skill_subgraph`
- `reject` → `__end__`

### 7.2 Checkpointing

- `SqliteSaver` for persistent checkpoints
- `thread_id` = `"{source}_{job_id}"` (same as current)
- Checkpoint after every node transition
- Resume from any breakpoint with `--resume`

### 7.3 Graph Assembly

```python
# src/graph.py

def build_pipeline_graph(
    *,
    workspace: WorkspaceManager,
    checkpointer: BaseCheckpointSaver | None = None,
    match_chain: Runnable | None = None,
    gen_chain: Runnable | None = None,
) -> CompiledGraph:
    """Assemble the full pipeline graph."""

    workflow = StateGraph(GraphState)

    # Tool nodes (deterministic)
    workflow.add_node("scrape", make_scrape_node(workspace))
    workflow.add_node("translate", make_translate_node(workspace))
    workflow.add_node("extract_bridge", make_extract_bridge_node(workspace))

    # Skill nodes (LLM)
    workflow.add_node("match_skill", build_match_skill_subgraph(workspace=workspace, chain=match_chain))
    workflow.add_node("generate_documents", make_generate_documents_node(workspace=workspace, chain=gen_chain))

    # Tool nodes (post-generation)
    workflow.add_node("render", make_render_node(workspace))
    workflow.add_node("package", make_package_node(workspace))

    # Edges
    workflow.add_edge(START, "scrape")
    workflow.add_edge("scrape", "translate")
    workflow.add_edge("translate", "extract_bridge")
    workflow.add_edge("extract_bridge", "match_skill")
    # match_skill routes internally via Command
    workflow.add_edge("generate_documents", "render")
    workflow.add_edge("render", "package")
    workflow.add_edge("package", END)

    return workflow.compile(
        checkpointer=checkpointer or InMemorySaver(),
        interrupt_before=["match_skill"],  # top-level HITL gate
    )
```

### 7.4 Match Skill as Subgraph

The match_skill keeps its internal graph structure (load_inputs → run_llm → persist_round → human_review → apply_decision → prepare_regeneration). It is composed into the top-level graph as a subgraph node. When it finishes (approve or reject), control returns to the parent graph.

The `generate_documents` node fires after match_skill approval. It is no longer embedded inside match_skill — it's a peer node in the top-level graph. This resolves the orchestration ambiguity documented in `future_docs/issues/orchestration.md`.

---

## 8. Layer 4: Textual TUI

### 8.1 Design Intent

The TUI is the operator interface for the HITL review loop. It connects to the LangGraph graph via `MatchBus` (already exists in `src/review_ui/bus.py`) and displays the `ReviewSurface` for decision-making.

### 8.2 Generalized Review Pattern

Currently, only match_skill has a review gate. The design anticipates that other nodes may get review gates too (generate_documents already produces deterministic review indicators). The review pattern should be generalizable:

1. A node writes a `ReviewSurface` to `nodes/{node}/review/current.json`
2. The graph pauses at an `interrupt_before` breakpoint
3. The TUI loads the review surface, displays it, collects decisions
4. The TUI resumes the graph with a `ReviewPayload`
5. The node validates the payload and routes accordingly

For now, the TUI only handles match_skill review. But the `ReviewSurface` and `ReviewPayload` contracts should live in `src/core/contracts.py` so they can be reused by any node that adds a review gate.

### 8.3 Module Path Fix

The current `src/review_ui/` has broken import paths (`src.ui.*` instead of `src.review_ui.*`). The move to `src/ui/` fixes this — the imports become correct by matching the directory name. The `MatchBus` stays as-is but gains a `workspace` parameter so it reads from the unified data plane instead of constructing its own `MatchArtifactStore`.

### 8.4 Future: Recovering the Other UI Branch

There is UI work on other branches. This design prioritizes getting the pipeline working end-to-end with the existing TUI. The other UI work can be integrated later on top of the same `MatchBus` → LangGraph → workspace stack.

---

## 9. Compatibility: Output → Input Chain

This section documents the exact format transformations between pipeline steps, confirming compatibility.

### 9.1 Scraper → Translator

| Field | Scraper output | Translator input | Compatible? |
|-------|---------------|-----------------|-------------|
| Format | `JobPosting` JSON + `content.md` | `extracted_data.json` + `content.md` | Yes — same files |
| Path | `nodes/scrape/proposed/` | Reads from scrape's output path | Yes — via artifact_refs |

### 9.2 Translator → Extract Bridge

| Field | Translator output | Bridge input | Compatible? |
|-------|------------------|--------------|-------------|
| Format | `extracted_data_en.json` (translated JobPosting) | Reads `requirements` field (list of strings) | Yes |
| Transform | None needed | Assigns IDs: `REQ_001`, `REQ_002`, ... | Deterministic |

### 9.3 Extract Bridge → Match Skill

| Field | Bridge output | Match input | Compatible? |
|-------|--------------|-------------|-------------|
| Format | `list[RequirementInput]` (id, text, priority) | `state.requirements` as `list[dict]` | Yes — Pydantic-validated in match node |
| Profile | Loaded from reference_data at pipeline start | `state.profile_evidence` as `list[dict]` | Yes |

### 9.4 Match Skill → Generate Documents

| Field | Match output | Generate input | Compatible? |
|-------|-------------|----------------|-------------|
| Format | `approved/state.json` (MatchEnvelope) | Reads from disk via artifact_refs | Yes |
| Profile | Already in state | Same | Yes |
| Requirements | Already persisted by match | Reads for enrichment (requirement_text) | Yes |

### 9.5 Generate Documents → Render

| Field | Generate output | Render input | Compatible? |
|-------|----------------|--------------|-------------|
| Format | `cv.md`, `cover_letter.md` (Markdown) | `RenderRequest` with markdown source path | Yes |
| Engine | N/A | tex or docx (configurable) | N/A |

### 9.6 Render → Package

| Field | Render output | Package input | Compatible? |
|-------|--------------|---------------|-------------|
| Format | PDF/DOCX files | Copies to `final/`, computes manifest | Yes |

---

## 10. Testing Strategy

### 10.1 Unit Tests (per module)

Each module's `run()` entrypoint is tested in isolation using a `tmp_path` workspace:

```python
def test_scraper_run(tmp_path):
    ws = WorkspaceManager(tmp_path)
    refs = scraper.run(source="test", job_id="1", workspace=ws, source_url="...")
    assert (tmp_path / "test/1/nodes/scrape/proposed/state.json").exists()
```

### 10.2 Integration Tests (pipeline segments)

Test adjacent pairs: scrape → translate, translate → extract_bridge, extract_bridge → match, etc. Each test writes the upstream output to a `tmp_path` workspace, then runs the downstream module.

### 10.3 End-to-End Tests (full pipeline)

Once the pipeline runs end-to-end, add a full E2E test that:
1. Uses a fixture job posting (or a mock scraper)
2. Runs the full graph
3. Validates that `final/manifest.json` exists with all expected artifacts
4. Checks hash integrity

### 10.4 TestSprite Integration

After E2E tests pass, define behaviour rules for each node:
- **Scraper:** Given a URL, must produce `state.json` with all MANDATORY JobPosting fields
- **Translator:** Given non-English input, must produce `_en.json` with translated fields
- **Match:** Given requirements + evidence, must produce MatchEnvelope with scores and reasoning
- **Generate:** Given approved matches, must produce cv.md, cover_letter.md, email_body.txt
- **Render:** Given markdown, must produce PDF
- **Package:** Given rendered docs, must produce manifest with SHA256 integrity

These rules can be fed to TestSprite for automated pipeline testing.

---

## 11. Implementation Sequence

This is a long-running plan implemented in steps. Each step produces a working (if partial) pipeline.

### Step 1: Core IO Layer
- Port `WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService` from dev branch to `src/core/io/`
- Port `RoundManager` to `src/core/round_manager.py`
- Port `GraphState`, `RunStatus`, `ErrorContext` to `src/core/state.py`
- Write unit tests for core IO

### Step 2: Module Reorganization
- Move `src/scraper/` → `src/tools/scraper/`
- Move `src/match_skill/` → `src/skills/match_skill/`
- Move `src/generate_documents/` → `src/skills/generate_documents/`
- Move `src/review_ui/` → `src/ui/`
- Update all import paths
- Verify existing tests still pass

### Step 3: Wire Tools to Core IO
- Update scraper to write output via `WorkspaceManager` (to `nodes/scrape/proposed/`)
- Update translator to read/write via `WorkspaceManager`
- Update render to read/write via `WorkspaceManager`
- Each tool gets a `run()` entrypoint with the standard signature

### Step 4: Wire Skills to Core IO
- Update `match_skill` storage to delegate to `ArtifactWriter` + `WorkspaceManager`
- Update `generate_documents` to read match output via `ArtifactReader` (no more hardcoded `MatchArtifactStore()`)
- Both skills accept `workspace` parameter

### Step 5: Extract Bridge
- Implement deterministic `bridge_extract()` in `src/skills/extract_understand/bridge.py`
- Transforms `JobPosting.requirements` (strings) → `RequirementInput` (id + text)
- Write tests

### Step 6: Top-Level Graph
- Implement `src/graph.py` with the full pipeline topology
- Wire tool-nodes and skill-subgraph
- Test with `InMemorySaver` (no persistence)
- Test HITL pause/resume flow

### Step 7: Unified CLI
- Implement `src/cli/main.py` with subcommands
- `pipeline` command: builds graph, runs or resumes
- Standalone commands delegate to module entrypoints
- Test CLI end-to-end

### Step 8: Fix TUI Wiring
- Move to `src/ui/`, fix import paths
- Update `MatchBus` to accept `workspace` parameter
- Wire `review` CLI command to launch TUI against a paused graph
- Move `ReviewSurface` / `ReviewPayload` to `src/core/contracts.py`

### Step 9: End-to-End Testing
- Write full pipeline integration test
- Verify artifact chain: scrape → translate → extract → match → generate → render → package
- Define TestSprite behaviour rules for each node

### Step 10: Cleanup
- Delete resolved `future_docs/issues/` entries (orchestration, review_ui_wiring, testing_and_data_management)
- Update CLAUDE.md with new module layout and commands
- Update all module READMEs
- Update `docs/runtime/pipeline_overview.md`

---

## 12. What This Design Does NOT Do

- **Port extract_understand LLM logic** — deferred, documented in `future_docs/new_feature/extract_understand_node.md`
- **Build review gates for all nodes** — only match_skill has one now; the pattern is generalizable but not implemented for other nodes yet
- **Create a shared utils folder** — deliberately deferred; extract when patterns repeat
- **Implement the full dev branch pipeline** — nodes like `build_application_context`, `tailor_cv`, `draft_email` are not implemented (they don't exist on dev either)
- **Recover the other branch's UI** — this design makes it possible but doesn't do it now
- **Optimize scraper for LangGraph** — scraper is async with crawl4ai; wrapping it as a sync LangGraph node is intentionally simple (run async in thread)

---

## 13. Open Questions

1. **Scraper async wrapping:** The scraper uses `asyncio` + `crawl4ai`. LangGraph nodes are sync by default. The simplest approach: `asyncio.run()` inside the tool-node wrapper. Is there a reason to keep it async end-to-end?

2. **Profile evidence path:** Currently at `/home/jp/phd-workspaces/legacy/data/reference_data/`. Should this be configurable via CLI flag, or hardcoded as a project constant? The CLI already supports `--profile-evidence` for a path.

3. **LangGraph Studio exposure:** The current `langgraph.json` exposes `match_skill` only. Should the unified pipeline graph also be exposed to Studio? If so, it needs a `create_studio_graph()` factory.

---

## 14. Consolidating the Issues

This design, once implemented, resolves the three open issues:

| Issue | How resolved |
|-------|-------------|
| `future_docs/issues/orchestration.md` | Top-level graph defines the pipeline topology. `generate_documents` is a peer node, not embedded in `match_skill`. |
| `future_docs/issues/review_ui_wiring.md` | TUI moves to `src/ui/`, import paths fixed, `MatchBus` wired to `WorkspaceManager`. |
| `future_docs/issues/testing_and_data_management.md` | `WorkspaceManager` is the single IO layer. All modules use it. Cross-module fixtures use `tmp_path` workspaces. `generate_documents` reads match output via `ArtifactReader`, not a hardcoded store. |
