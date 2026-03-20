# Phase 4: CLI Integration + Checkpointing

## Context for subagent

You are continuing the LangGraph pipeline migration at `/home/jp/phd`. Phases 0-3 built the full graph with all 9 nodes. The graph compiles and runs end-to-end in tests (with mocks). Now you need to make it usable from the CLI with persistent checkpointing so users can:

1. Start a pipeline run: `pipeline job <id> graph-run`
2. Graph pauses at review_gate (writes proposal to disk)
3. User edits proposal in Obsidian (external to CLI)
4. Resume: `pipeline job <id> graph-run --resume`
5. Graph continues (or loops back if edits detected)

**Read before starting:**
- `docs/plans/2026-03-03-langgraph-pipeline/00-overview.md` — full migration overview
- `src/graph/pipeline.py` — compiled graph with all nodes
- `src/graph/state.py` — `ApplicationState` TypedDict
- `src/cli/pipeline.py` — existing CLI dispatcher (currently ~1130 lines)
- `src/cli/README.md` — CLI documentation
- `src/utils/state.py` — `JobState` for path resolution

## Objectives

1. Add SQLite checkpointer for state persistence across CLI sessions
2. Add `graph-run` command to start/resume graph execution
3. Add `graph-status` command to inspect current graph state
4. Handle the interrupt/resume UX cleanly in the CLI

## What to do

### 1. Add SQLite checkpointer to `src/graph/__init__.py`

```python
from langgraph.checkpoint.sqlite import SqliteSaver

def compile_pipeline(job_dir: Path | None = None) -> CompiledGraph:
    """Compile the pipeline graph with optional persistent checkpointing.

    Args:
        job_dir: If provided, use SQLite checkpointer at {job_dir}/.graph/checkpoints.db.
                 If None, use MemorySaver (for testing).
    """
    from src.graph.pipeline import build_graph

    builder = build_graph()

    if job_dir is not None:
        db_dir = job_dir / ".graph"
        db_dir.mkdir(parents=True, exist_ok=True)
        checkpointer = SqliteSaver.from_conn_string(
            f"sqlite:///{db_dir / 'checkpoints.db'}"
        )
    else:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)
```

Thread ID convention: `thread_id = f"{source}/{job_id}"` — one thread per job.

### 2. Add `graph-run` command to CLI

In `src/cli/pipeline.py`, add a new subcommand:

```
pipeline job <job_id> graph-run [--resume] [--language LANG] [--via ENGINE] [--template STYLE]
```

**Implementation:**

```python
def handle_graph_run(args):
    """Run the LangGraph pipeline for a job."""
    from src.graph import compile_pipeline
    from src.utils.state import JobState

    job_state = JobState(args.job_id, args.source)
    graph = compile_pipeline(job_dir=job_state.job_dir)
    config = {"configurable": {"thread_id": f"{args.source}/{args.job_id}"}}

    if args.resume:
        # Resume from interrupt
        from langgraph.types import Command
        result = graph.invoke(Command(resume=True), config=config)
    else:
        # Fresh run
        initial_state = {
            "job_id": args.job_id,
            "source": args.source,
            "review_round": 0,
            "force": args.force,
            "language": getattr(args, "language", "english"),
            "render_via": getattr(args, "via", "docx"),
            "docx_template": getattr(args, "template", "modern"),
            "comments": [],
        }
        result = graph.invoke(initial_state, config=config)

    # Check if interrupted (review gate)
    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"]
        proposal_path = interrupt_data[0].value.get("proposal_path", "unknown")
        review_round = interrupt_data[0].value.get("review_round", 0)
        print(f"\n--- Review Required (round {review_round + 1}) ---")
        print(f"Edit the proposal at: {proposal_path}")
        print(f"Then resume with: pipeline job {args.job_id} graph-run --resume")
        return 0

    # Completed
    final_pdf = result.get("final_pdf_path")
    if final_pdf:
        print(f"\nPipeline complete. Final PDF: {final_pdf}")
    return 0
```

**Argument parser additions:**
- Add `graph-run` as a job verb alongside existing verbs
- Add `--resume` flag (action="store_true")
- Reuse existing `--language`, `--via`, `--template` flags

### 3. Add `graph-status` command

```
pipeline job <job_id> graph-status
```

**Implementation:**

```python
def handle_graph_status(args):
    """Show current graph execution state for a job."""
    from src.graph import compile_pipeline
    from src.utils.state import JobState

    job_state = JobState(args.job_id, args.source)
    db_path = job_state.job_dir / ".graph" / "checkpoints.db"

    if not db_path.exists():
        print(f"No graph state for job {args.job_id}. Run 'graph-run' first.")
        return 1

    graph = compile_pipeline(job_dir=job_state.job_dir)
    config = {"configurable": {"thread_id": f"{args.source}/{args.job_id}"}}

    # Get current state from checkpoint
    state = graph.get_state(config)

    print(f"Job: {args.job_id}")
    print(f"Graph status: {state.next}")  # next node(s) to execute
    print(f"Review round: {state.values.get('review_round', 0)}")

    if state.next:
        print(f"Waiting at: {', '.join(state.next)}")
        if "review_gate" in state.next or any("interrupt" in str(t) for t in (state.tasks or [])):
            proposal_path = state.values.get("proposal_path", "unknown")
            print(f"  Proposal to review: {proposal_path}")
            print(f"  Resume with: pipeline job {args.job_id} graph-run --resume")
    else:
        print("Pipeline completed.")
        final_pdf = state.values.get("final_pdf_path")
        if final_pdf:
            print(f"Final PDF: {final_pdf}")

    return 0
```

### 4. Add `.graph/` to `.gitignore`

Add `**/.graph/` to the project `.gitignore` — checkpoint databases are ephemeral runtime state, not versioned.

### 5. Handle error cases in CLI

- If `--resume` but no checkpoint exists → clear error message
- If graph raises during a node → print which node failed, preserve checkpoint so user can retry
- If LLM call fails → graph state is preserved at the failed node, user can retry with `--resume`

### 6. Update CLI README

Add the new commands to `src/cli/README.md`:

```markdown
## Graph-based Pipeline (New)

### Run full pipeline
```bash
pipeline job <id> graph-run [--language english] [--via docx] [--template modern]
```

Pipeline runs until it needs human review, then pauses. Edit the proposal in Obsidian, then resume:

```bash
pipeline job <id> graph-run --resume
```

### Check pipeline status
```bash
pipeline job <id> graph-status
```

Shows current graph state: which node is pending, review round, and resume instructions.
```

## What NOT to do

- Do NOT remove or modify existing step-based commands (`job <id> ingest`, `job <id> match`, etc.) — they must keep working
- Do NOT make `graph-run` the default for `job <id> run` — that happens in Phase 5
- Do NOT modify graph nodes — they are complete from Phases 2-3
- Do NOT implement complex error recovery (retry logic, partial reruns) — keep it simple: if a node fails, checkpoint preserves state, user reruns
- Do NOT store secrets or API keys in the checkpoint DB

## Completion criteria

The phase is done when:
1. `pipeline job <id> graph-run` starts a fresh pipeline run and pauses at review_gate
2. `pipeline job <id> graph-run --resume` continues from the checkpoint
3. `pipeline job <id> graph-status` shows current state correctly
4. SQLite checkpoint DB is created at `{job_dir}/.graph/checkpoints.db`
5. `.graph/` is in `.gitignore`
6. **Resume across sessions test**: start graph, kill CLI, restart, resume → continues from checkpoint
7. **Error recovery test**: mock a node failure, verify checkpoint preserves state at the failed node
8. `src/cli/README.md` documents the new commands
9. All existing CLI tests pass: `pytest tests/cli/test_pipeline.py`
10. `pytest tests/graph/` all pass (add CLI integration tests)

## Commit

```
feat: add graph-run CLI with SQLite checkpointing

- pipeline job <id> graph-run starts LangGraph pipeline execution
- Pauses at review_gate with interrupt(), prints review instructions
- pipeline job <id> graph-run --resume continues from checkpoint
- pipeline job <id> graph-status shows current graph state
- SQLite checkpointer persists state at {job_dir}/.graph/checkpoints.db
- .graph/ added to .gitignore
```

Update `changelog.md`:
```
## 2026-03-03 — LangGraph Pipeline Migration: Phase 4 (CLI + Checkpointing)

- Added `pipeline job <id> graph-run` command to execute the LangGraph pipeline.
- Graph pauses at review gate with `interrupt()`, prints proposal path and resume instructions.
- Added `--resume` flag to continue from checkpoint after human review.
- Added `pipeline job <id> graph-status` to inspect current graph execution state.
- SQLite checkpointer persists graph state at `{job_dir}/.graph/checkpoints.db` for cross-session resume.
- Added `.graph/` to `.gitignore`.
- Updated CLI documentation in `src/cli/README.md`.
```
