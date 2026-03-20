# Phase 3: Implement Remaining Nodes + CV Subgraph

## Context for subagent

You are continuing the LangGraph pipeline migration at `/home/jp/phd`. Phases 0-2 created the graph skeleton, extracted parsers/agents, and implemented the core nodes (ingest → match → keywords → review). Now you implement the remaining 5 nodes: motivate, email, tailor_cv (as a proper LangGraph subgraph), render, and package.

**Read before starting:**
- `docs/plans/2026-03-03-langgraph-pipeline/00-overview.md` — full migration overview
- `src/graph/pipeline.py` — current graph with 4 real nodes + 5 stubs
- `src/graph/agents/base.py` — `AgentRunner` (shared agent infra)
- `src/graph/agents/{matcher,seller,checker}.py` — per-agent wrappers
- `src/steps/motivation.py` — existing motivation step to wrap
- `src/steps/motivation_service.py` — `MotivationLetterService` (untracked, the actual service)
- `src/steps/email_draft.py` — existing email step to wrap
- `src/steps/cv_tailoring.py` — existing CV tailoring step (wraps `CVTailoringPipeline`)
- `src/steps/rendering.py` — existing render step to wrap
- `src/steps/packaging.py` — existing package step to wrap
- `src/utils/cv_rendering.py` — `build_cv()`, `build_to_render_markdown()`
- `src/render/docx.py` — `DocumentRenderer`

## Objectives

1. Implement `motivate` node
2. Implement `email` node
3. Implement `tailor_cv` node as a LangGraph subgraph (matcher → seller → checker)
4. Implement `render` node
5. Implement `package` node
6. Wire all edges and verify full graph end-to-end

## What to do

### 1. Implement `src/graph/nodes/motivate.py`

```python
def motivate(state: ApplicationState) -> dict:
    """Generate motivation letter from job posting + approved claims."""
```

- Create `JobState` from state
- Verify `planning/reviewed_mapping.json` exists (error if not — requires review)
- Call `MotivationLetterService().generate_for_job(state["job_id"], state["source"])`
- Extract comments from previous outputs, log them
- Read the generated files and return:
  ```python
  {
      "motivation_letter_md": letter_content,
      "motivation_data": structured_output_dict,
  }
  ```
- Disk artifacts: `planning/motivation_letter.md`, `planning/motivation_letter.json`

### 2. Implement `src/graph/nodes/email.py`

```python
def email(state: ApplicationState) -> dict:
    """Generate application email draft."""
```

- Create `JobState` from state
- Verify `planning/motivation_letter.json` exists (error if not — requires motivate)
- Call `MotivationLetterService().generate_email_draft(state["job_id"], state["source"])`
- Return `{"email_draft_md": email_content}`
- Disk artifact: `planning/application_email.md`

### 3. Implement `src/graph/nodes/tailor_cv.py` — LangGraph subgraph

This is the key architectural piece. The 3-agent chain (matcher → seller → checker) becomes its own `StateGraph`.

**Define subgraph state:**
```python
class CVTailoringSubstate(TypedDict):
    # Shared with parent
    job_id: str
    source: str
    job_posting: dict | None
    reviewed_claims: list[dict]

    # Subgraph-private
    agent_context: str              # initial context JSON for agents
    matcher_output: dict | None     # PipelineState from matcher
    seller_output: dict | None      # PipelineState from seller
    checker_output: dict | None     # PipelineState from checker

    # Output (shared with parent)
    proposed_claims: list[dict]
    to_render_md: str
```

**Define 3 subgraph nodes:**

```python
def matcher_agent(state: CVTailoringSubstate) -> dict:
    """Run MATCHER agent: job + profile → requirement mapping."""
    runner = AgentRunner()
    # Build context from job_posting + profile
    # Call run_matcher(runner, context)
    # Save intermediate: cv/pipeline_intermediates/01_matcher.json
    return {"matcher_output": result.model_dump()}

def seller_agent(state: CVTailoringSubstate) -> dict:
    """Run SELLER agent: mapping → tailored claims."""
    runner = AgentRunner()
    # Call run_seller(runner, matcher_json)
    # Save intermediate: cv/pipeline_intermediates/02_seller.json
    return {"seller_output": result.model_dump()}

def checker_agent(state: CVTailoringSubstate) -> dict:
    """Run REALITY-CHECKER agent: claims → verified claims."""
    runner = AgentRunner()
    # Call run_checker(runner, seller_json)
    # Save intermediate: cv/pipeline_intermediates/03_reality_checker.json
    return {"checker_output": result.model_dump()}
```

**Compile subgraph:**
```python
cv_builder = StateGraph(CVTailoringSubstate)
cv_builder.add_node("matcher_agent", matcher_agent)
cv_builder.add_node("seller_agent", seller_agent)
cv_builder.add_node("checker_agent", checker_agent)
cv_builder.add_edge(START, "matcher_agent")
cv_builder.add_edge("matcher_agent", "seller_agent")
cv_builder.add_edge("seller_agent", "checker_agent")
cv_builder.add_edge("checker_agent", END)
cv_subgraph = cv_builder.compile()
```

**Wrapper node for parent graph:**
```python
def tailor_cv(state: ApplicationState) -> dict:
    """Run CV tailoring 3-agent subgraph."""
    job_state = JobState(state["job_id"], state["source"])

    # Transform parent state → subgraph state
    substate = {
        "job_id": state["job_id"],
        "source": state["source"],
        "job_posting": state.get("job_posting"),
        "reviewed_claims": state.get("reviewed_claims", []),
        "agent_context": "",  # built inside matcher_agent
        "matcher_output": None,
        "seller_output": None,
        "checker_output": None,
        "proposed_claims": [],
        "to_render_md": "",
    }

    result = cv_subgraph.invoke(substate)

    # Write planning/cv_tailoring.md and cv/to_render.md
    # (extract from checker_output → approved claims → render markdown)
    # Use build_to_render_markdown from src/utils/cv_rendering.py as fallback

    return {
        "proposed_claims": result["proposed_claims"],
        "to_render_md": result["to_render_md"],
    }
```

**Register in parent graph:** Add `tailor_cv` as a regular node (not `add_node("tailor_cv", cv_subgraph)` — use the wrapper to handle state transformation).

### 4. Implement `src/graph/nodes/render.py`

```python
def render(state: ApplicationState) -> dict:
    """Render CV and motivation letter to PDF."""
```

- Create `JobState` from state
- Verify `cv/to_render.md` exists
- Call `build_cv()` from `src/utils/cv_rendering.py` with `via=state["render_via"]`, `template=state["docx_template"]`
- If `planning/motivation_letter.md` exists, render motivation PDF (via MotivationLetterService.build_pdf_for_job or a simpler markdown→PDF path)
- Return `{"rendered_paths": ["output/cv.pdf", "output/motivation_letter.pdf"]}`
- Disk artifacts: `output/cv.pdf`, `output/cv.docx` (intermediate), optionally `output/motivation_letter.pdf`

### 5. Implement `src/graph/nodes/package.py`

```python
def package(state: ApplicationState) -> dict:
    """Merge rendered PDFs into final application."""
```

- Create `JobState` from state
- Gather PDFs from `state["rendered_paths"]`
- Merge via PyPDF2 (reuse logic from `src/steps/packaging.py::_merge_pdfs`)
- Compress via ghostscript (reuse `_compress_pdf`)
- Return `{"final_pdf_path": "output/Final_Application.pdf"}`

### 6. Update `src/graph/pipeline.py`

Replace all remaining stubs with imports from real node modules. The full graph should now compile and execute end-to-end.

Verify edge wiring:
```python
builder.add_edge(START, "ingest")
builder.add_edge("ingest", "match")
builder.add_edge("match", "keywords")
builder.add_edge("keywords", "review_gate")
builder.add_conditional_edges("review_gate", after_review, {
    "match": "match",
    "motivate": "motivate",
})
builder.add_edge("motivate", "email")
builder.add_edge("review_gate", "tailor_cv")  # parallel path from review
builder.add_edge("tailor_cv", "render")
builder.add_edge("email", "package")
builder.add_edge("render", "package")
builder.add_edge("package", END)
```

**Important edge consideration:** Both `motivate → email → package` and `tailor_cv → render → package` feed into `package`. LangGraph handles this: `package` runs once both predecessors complete. If this creates issues with state merging, use a simple join node before package that collects `rendered_paths` and `email_draft_md`.

## What NOT to do

- Do NOT modify the 4 nodes from Phase 2 (ingest, match, keywords, review)
- Do NOT modify `src/steps/` files — they stay as-is for backwards compat
- Do NOT modify `src/cli/pipeline.py` — CLI integration is Phase 4
- Do NOT implement checkpointing — that's Phase 4
- Do NOT change the rendering infrastructure (`src/render/`) — just call it
- Do NOT add new agent prompts — reuse the existing ones from `src/prompts/cv_multi_agent.txt`

## Completion criteria

The phase is done when:
1. All 9 nodes are implemented (no more stubs)
2. The CV tailoring subgraph compiles independently and can be tested in isolation
3. **Subgraph isolation test**: invoke CV subgraph with mock Gemini → produces `proposed_claims` and `to_render_md`
4. **Full graph end-to-end test** (with mocks): invoke from START, interrupt at review, resume with approvals, run through all remaining nodes to END
5. **Artifact persistence test**: verify all expected files written to disk:
   - `planning/motivation_letter.md`, `planning/motivation_letter.json`
   - `planning/application_email.md`
   - `planning/cv_tailoring.md`, `cv/to_render.md`
   - `cv/pipeline_intermediates/{01_matcher,02_seller,03_reality_checker}.json`
   - `output/cv.pdf`, `output/Final_Application.pdf`
6. All existing tests still pass: `pytest tests/ -x --ignore=tests/graph`
7. `pytest tests/graph/` all pass

## Commit

```
feat: implement remaining graph nodes and CV tailoring subgraph

- motivate node wraps MotivationLetterService
- email node generates application email draft
- tailor_cv implemented as LangGraph subgraph (matcher → seller → checker)
- render node calls existing rendering infrastructure
- package node merges and compresses PDFs
- Full graph now executable end-to-end (9 nodes, all edges wired)
```

Update `changelog.md`:
```
## 2026-03-03 — LangGraph Pipeline Migration: Phase 3 (Remaining Nodes + CV Subgraph)

- Implemented `motivate` and `email` nodes wrapping existing services.
- Implemented `tailor_cv` as a LangGraph subgraph with 3 agent nodes (matcher → seller → checker), independently compilable and testable.
- Implemented `render` and `package` nodes wrapping existing rendering and PDF infrastructure.
- Full pipeline graph now executable end-to-end: 9 nodes, conditional review loop, CV tailoring subgraph.
- Added end-to-end graph tests with mocked LLM responses.
```
