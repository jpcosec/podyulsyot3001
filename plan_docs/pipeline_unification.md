# Pipeline Unification Implementation Plan

**Goal:** Orchestrate all modules under a single LangGraph pipeline with unified CLI and proper TUI wiring.
**Based on:** `docs/superpowers/specs/2026-03-29-pipeline-unification-design.md`
**Corrections applied:** Gemini's architectural review + Claude's counter-proposal

---

## Constraints

- **"Orchestrating now, not upgrading logic"** — do not rewrite module internals, only wire them together
- **Preserve existing module READMEs** — update after implementation, not before
- **Async-native pipeline** — avoid `asyncio.run()` in sync nodes; use async throughout
- **Studio-compatible state** — carry summary payloads in GraphState, not just refs
- **Respect docs/standards/** — follow conventions from `docs/standards/docs/` and `docs/standards/code/`

---

## Open Questions (RESOLVED)

1. **Subgraph interrupt routing:** ✅ Obtain config via `app.get_state(config)` — it contains the exact nested thread_id needed to inject payload into subgraph
2. **Profile evidence path:** ✅ Parameter injected at pipeline init, CLI flag override, `.env` fallback — never hardcoded in node logic
3. **Studio exposure:** ✅ Yes — add unified graph to `langgraph.json` after Stage 5 passes

---

## Implementation Stages

### Stage 1: Extract Bridge (Trivial)

**Goal:** Transform scraper output to match_skill input without fragility.

**⚠️ Critical: I/O path crossing**
Current modules write to different directories:
- Scraper/Translator → `data/source/<source>/<job_id>/`
- Match Skill → `output/match_skill/<source>/<job_id>/`

The bridge MUST physically copy files between these directories until Stage 6 unifies I/O.

**What:**
- Read from `data/source/<source>/<job_id>/extracted_data_en.json` (or `extracted_data.json` if not translated)
- Map `JobPosting.requirements` (already `List[str]`) to `RequirementInput` with `id="REQ_001"`, `text=<string>`, `priority="must"`
- Write to `output/match_skill/<source>/<job_id>/nodes/extract_bridge/proposed/state.json`
- Also copy relevant files (content.md) to `output/match_skill/.../nodes/extract_bridge/proposed/`

**Fragility handling:**
```python
def extract_bridge(source: str, job_id: str) -> list[RequirementInput]:
    try:
        data = json.load(open(f"data/source/{source}/{job_id}/extracted_data_en.json"))
        requirements = data.get("requirements", [])
        if not requirements:
            raise ValueError("No requirements field in JobPosting")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        # Return dummy requirement so graph continues — HITL reviewer will see error
        logger.warning(f"{LogTag.WARN} Extract bridge failed: {e}, returning dummy")
        return [RequirementInput(id="REQ_ERROR", text=f"[ERROR: {e}]", priority="must")]
    
    return [
        RequirementInput(id=f"REQ_{i:03d}", text=req, priority="must")
        for i, req in enumerate(requirements, 1)
    ]
```

**Why first:** It's a 10-line function. Validates the contract chain without touching other modules.

**Verify:**
- `JobPosting.requirements` field exists and is populated
- Output matches `RequirementInput` schema in `src/ai/match_skill/contracts.py`
- Files exist in both `data/source/` and `output/match_skill/` after bridge runs

---

### Stage 2: Top-Level Graph (Wiring Only)

**Goal:** Connect existing modules into a LangGraph pipeline without rewriting I/O.

**⚠️ Critical: Never call main.py from nodes**
Calling `asyncio.to_thread(main)` is dangerous because:
- `main` invokes `logging.basicConfig(force=True)` which destroys the orchestrator's logging
- It couples orchestration to CLI (argparse strings instead of Python types)

**Solution:** Import and call business logic classes directly.

**What:**
- Create `src/graph.py` — top-level `StateGraph`
- Wire: `scrape → translate → extract_bridge → match_skill → generate_documents → render → package`

**Key decision:** Do NOT move modules to new directories. Keep:
- `src/ai/scraper/`
- `src/ai/match_skill/`
- `src/ai/generate_documents/`
- `src/tools/translator/`
- `src/tools/render/`

**Node wrappers (correct pattern):**

```python
async def scrape_node(state: GraphState) -> dict:
    # ✅ Call adapters/services directly — NOT main.py
    from src.ai.scraper.providers import PROVIDERS
    from src.ai.scraper.smart_adapter import SmartScraperAdapter
    
    adapter = PROVIDERS[state["source"]]
    result = await adapter.run(
        source=state["source"],
        job_id=state["job_id"],
        source_url=state.get("source_url"),
        # ... adapter-specific params
    )
    
    return {
        "artifact_refs": {
            "scrape_state": f"data/source/{state['source']}/{state['job_id']}/extracted_data.json",
            "scrape_content": f"data/source/{state['source']}/{state['job_id']}/content.md",
        },
        "current_node": "scrape"
    }
```

**For match_skill (subgraph):**

```python
def make_match_skill_subgraph(workspace: WorkspaceManager):
    # Import existing graph factory
    from src.ai.match_skill.graph import build_match_skill_graph
    from langgraph.checkpoint.memory import MemorySaver
    
    return build_match_skill_graph(
        artifact_store=workspace,  # or pass refs
        checkpointer=MemorySaver(),
    )
```

**GraphState design:**

```python
class GraphState(TypedDict, total=False):
    source: str
    job_id: str
    run_id: str
    current_node: str
    status: RunStatus
    
    # Summary payloads (for Studio inspection + refs for durability)
    requirements: list[RequirementInput]
    profile_evidence: list[ProfileEvidence]
    match_result: MatchEnvelope | None
    
    # Artifact refs (full data on disk)
    artifact_refs: dict[str, str]
    
    error_state: ErrorContext | None
```

**Profile evidence injection:**
```python
def get_profile_evidence(path: str | None = None) -> list[ProfileEvidence]:
    path = path or os.getenv("PROFILE_EVIDENCE_PATH", "data/reference_data/profile/base_profile/profile_base_data.json")
    with open(path) as f:
        data = json.load(f)
    return [ProfileEvidence(**item) for item in data.get("evidence", [])]
```

**Verify:**
- Pipeline runs end-to-end with mock scraper input
- Checkpoint persists after each node
- `interrupt_before=["match_skill"]` pauses correctly
- Logging is NOT overwritten during execution

---

### Stage 3: Unified CLI

**Goal:** Single entry point for pipeline and standalone commands.

**What:**
- Create `src/cli/__init__.py`
- Create `src/cli/main.py` with argparse subcommands

**Commands:**

```
python -m src.cli.main pipeline --source stepstone --job-id 123 --source-url "..."
python -m src.cli.main scrape --source stepstone --limit 5
python -m src.cli.main match --source stepstone --job-id 123
python -m src.cli.main review --source stepstone --job-id 123
```

**Structure:**

```python
# src/cli/main.py
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="postulator")
    subparsers = parser.add_subparsers()
    
    subparsers.add_command("pipeline", help="Run full pipeline")
    subparsers.add_command("scrape", help="Run scraper only")
    # ...
    return parser
```

**Verify:**
- `--help` works for all commands
- `pipeline` command runs full graph
- Standalone commands work independently

---

### Stage 4: TUI Wiring Fix

**Goal:** Fix broken imports and wire TUI to pipeline graph.

**⚠️ Critical: Subgraph resume routing**
When `match_skill` runs as a subgraph inside the pipeline graph:
- `app.update_state(config, {"review_payload": ...}, as_node="human_review_node")` will fail
- Error: "node human_review_node not found"

**Solution:** Obtain the current state to get the nested thread_id:

```python
def get_resume_config(app, thread_id: str) -> dict:
    # Get current state — it contains the nested thread reference
    current_state = app.get_state({"configurable": {"thread_id": thread_id}})
    # The state metadata has the correct config for subgraph resume
    return current_state.config
```

**What:**
- Fix import paths in `src/review_ui/app.py` and `src/review_ui/screens/review_screen.py`
- Update `MatchBus.get_resume_config()` to obtain config from `app.get_state()`
- Update `MatchBus` to accept `artifact_refs` (from pipeline GraphState) instead of constructing its own store
- Wire `review` CLI command to launch TUI against paused thread

**Note:** Module path stays `src/review_ui/` — do NOT move to `src/ui/`. The design said `src/ui/` but that's a cosmetic change that breaks imports. Keep as-is.

**Verify:**
- `python -m src.cli.main review` launches TUI
- TUI loads `review/current.json`
- Resume payload routes correctly to subgraph via nested thread_id
- No "node not found" errors

---

### Stage 5: End-to-End Test

**Goal:** Verify full pipeline works with real (or mock) data.

**What:**
- Use a fixture job posting or mock scraper
- Run: pipeline start → HITL pause → resume → complete
- Validate all artifacts exist

**Verify:**
- `output/<source>/<job_id>/nodes/package/final/manifest.json` exists
- All intermediate artifacts present

---

### Stage 6: WorkspaceManager Migration (Post-MVP)

**Goal:** Unify I/O layer progressively.

**What:**
- Port WorkspaceManager from dev branch to `src/core/io/`
- Refactor modules to accept `workspace` parameter instead of constructing their own stores
- Migrate one module at a time, keeping pipeline working

**Strategy:**
1. Pass `workspace` to module entrypoints
2. Update `MatchArtifactStore` and `DocumentArtifactStore` to delegate to `ArtifactWriter`
3. Run E2E tests after each module migration

**Verify:**
- All modules use `WorkspaceManager` paths
- No hardcoded `output/` paths remain in module logic

---

### Stage 7: Schema Versioning & Hardening

**Goal:** Address `match_skill_hardening_roadmap.md` items.

**What:**
- Add `schema_version` to all persisted artifacts
- Implement evidence ranking before matching (if needed)
- Add LangSmith metadata tags

**Verify:**
- Artifacts include `schema_version` field
- Tests cover edge cases from roadmap

---

## Testing Strategy

### Unit Tests (per module wrapper)

Each node wrapper in `src/graph.py` is tested in isolation:

```python
@pytest.mark.asyncio
async def test_scrape_node_produces_refs():
    state = GraphState(source="test", job_id="1", ...)
    result = await scrape_node(state)
    assert "scrape_state_ref" in result["artifact_refs"]
```

### Integration Tests (module pairs)

Test adjacent pairs in `tests/integration/`:

| Test | Upstream | Downstream |
|------|----------|------------|
| `test_scrape_to_translate` | scraper output | translator input |
| `test_translate_to_bridge` | translator output | extract_bridge |
| `test_bridge_to_match` | bridge output | match_skill |
| `test_match_to_generate` | approved match | generate_documents |
| `test_generate_to_render` | generate output | render |

Each test:
1. Writes upstream output to `tmp_path`
2. Runs downstream module
3. Validates expected artifacts exist

### End-to-End Test

In `tests/e2e/`:

```python
@pytest.mark.asyncio
async def test_full_pipeline_with_review():
    # Run pipeline with interrupt_before match_skill
    # Simulate TUI review payload
    # Resume and complete
    # Assert final artifacts exist
```

### Test Coverage Contract

Per `docs/standards/code/llm_langgraph_methodology.md`:

- [ ] Approve flow: graph runs, pauses, resumes with approval, completes
- [ ] Regeneration flow: review requests regeneration, context prepared, second round runs
- [ ] Rejection flow: review rejects, graph ends cleanly
- [ ] Stale hash rejection: resume with mismatched hash is rejected
- [ ] Bare-Continue safety: resume with no payload returns to pending state

---

## Documentation Updates

Per `docs/standards/docs/documentation_and_planning_guide.md`:

1. **Update module READMEs** after each stage, not before:
   - `src/ai/scraper/README.md`
   - `src/ai/match_skill/README.md`
   - `src/ai/generate_documents/README.md`
   - `src/tools/translator/README.md`
   - `src/tools/render/README.md`
   - `src/review_ui/README.md`

2. **Update `docs/runtime/pipeline_overview.md`** to reflect unified pipeline

3. **Update `CLAUDE.md`** with:
   - New CLI commands
   - New file structure (`src/graph.py`, `src/cli/`)

4. **Delete resolved `future_docs/` entries** after completion:
   - `future_docs/issues/orchestration.md`
   - `future_docs/issues/review_ui_wiring.md` (if TUI fix works)
   - `future_docs/issues/testing_and_data_management.md` (if tests pass)

---

## Rollback Plan

If a stage fails:

| Stage | Rollback |
|-------|----------|
| 1-2 | Delete `src/graph.py`; modules work standalone |
| 3 | Delete `src/cli/`; use module CLIs directly |
| 4 | TUI remains broken; use CLI with `--review-payload` |
| 5 | Pipeline broken; run modules standalone |
| 6-7 | Revert to hardcoded paths; defer hardening |

---

## Success Criteria

- [ ] `python -m src.cli.main pipeline --source test --job-id 1` runs end-to-end
- [ ] `python -m src.cli.main review --source test --job-id 1` launches TUI
- [ ] All existing tests pass (`python -m pytest tests/ -q`)
- [ ] Module READMs updated with new CLI commands
- [ ] No broken imports in `src/review_ui/`
