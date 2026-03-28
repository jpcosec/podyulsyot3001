# Match Skill Implementation Methodology

This guide documents how the `match_skill` work was planned, implemented, validated, and operated during development.

## High-Level Approach

The work began by inspecting the `dev` branch match flow and separating two concerns:

- what product behavior had to be preserved,
- what custom implementation details could be replaced by more native LangGraph/LangChain patterns.

The strategy was to preserve the business behavior while replacing the framework plumbing.

## Planning Decisions

The implementation decisions were:

- keep deterministic review and regeneration logic custom,
- use LangGraph for orchestration, breakpoints, and routing,
- use LangChain for prompt + structured output,
- keep persisted artifacts JSON-first,
- expose the graph to Studio,
- make the system runnable even without model credentials for local graph debugging.

## Development Sequence

The work was performed roughly in this order:

1. inspect the `dev` branch match and review behavior,
2. define a cleaner LangGraph-native subgraph,
3. implement contracts and persistence first,
4. implement the LangChain prompt/model boundary,
5. implement the LangGraph node flow,
6. add a CLI runner for local operation,
7. expose the graph to Studio,
8. rebuild the environment from `requirements.txt`,
9. validate through tests, API runs, Studio interaction, and browser automation,
10. harden the review flow after discovering Studio-specific UX issues,
11. **build the Textual Review TUI** for improved HITL ergonomics,
12. **port and integrate the `generate_documents` node** as a post-approval follow-up.

## Studio Enablement Method

### Why Studio Needed Special Handling

Studio needed:

- a discoverable graph entry in `langgraph.json`,
- a graph factory that can load even without Gemini credentials,
- a local dev server that includes the Studio/runtime dependencies.

### What Was Added

- `langgraph.json`
- `create_studio_graph()` in `src/match_skill/graph.py`
- `langgraph-cli[inmem]` in `requirements.txt`

### Why A Demo Chain Was Added

Without credentials, Studio could render the topology but would fail when the model node executed.

To reduce friction during development, `create_studio_graph()` uses:

- the real Gemini chain if credentials exist,
- a deterministic demo chain otherwise.

This made it possible to validate the full graph lifecycle locally regardless of credential availability.

## Browser Interaction Method

### Why We Used The Browser Bridge

We wanted to do more than hit the API. We wanted to:

- open Studio,
- confirm the graph was visible,
- confirm the thread view was visible,
- inspect the actual live Studio UI.

### Setup That Was Needed

The browser bridge required:

```bash
npx @different-ai/opencode-browser install
```

Then:

- restart the CLI session,
- ensure the extension/backend is loaded,
- confirm the broker socket is reachable.

### What We Actually Verified

We verified:

- the broker was connected,
- tabs could be opened,
- the Studio URL loaded,
- the graph page showed the `match_skill` nodes,
- a live thread page could be navigated.

## Local Server Method

### Environment Rebuild

The local conda env was intentionally removed and recreated from `requirements.txt` to verify that the documented dependencies were sufficient.

That rebuild included:

- updated direct package versions,
- `langgraph-cli[inmem]`,
- `pytest`.

### Server Launch

The local server was launched with:

```bash
conda run -n phd-cv langgraph dev --config langgraph.json --no-browser --port 8124
```

This gave:

- local API,
- Studio connection target,
- interactive graph debugging.

## Validation Method

### Automated Validation

Automated tests were added first for the critical paths:

- approve,
- regenerate,
- stale review hash rejection,
- CLI run/resume,
- safe continue-without-payload behavior.

### API Validation

The graph was then exercised manually through the LangGraph API by:

1. discovering the assistant,
2. creating a thread,
3. starting a run,
4. inspecting thread state,
5. posting a structured review payload,
6. resuming execution,
7. checking the new state and artifact refs.

### Studio Validation

Studio was then used to confirm:

- the graph topology,
- connection state,
- pause at the review node,
- right-hand thread history,
- interaction with a live thread.

## Issue Discovered During Validation

One important issue was discovered during real Studio interaction:

- pressing `Continue` with no `review_payload` caused `apply_review_decision` to validate `None` and fail.

This was not just a theoretical concern; it was discovered through actual Studio usage.

### How It Was Fixed

`apply_review_decision` was updated so that:

- if `review_payload` is missing,
- the graph returns safely to `human_review_node`,
- the thread remains in `pending_review`,
- no crash occurs.

Then that behavior was turned into an automated test.

## Documentation Strategy

Documentation was handled in layers:

- inline pydoc docstrings inside the code,
- `src/match_skill/README.md` for local module usage,
- runtime docs under `docs/runtime/` for the full implementation and methodology.

This split exists because the code-level docs answer "what does this function do?" while the runtime docs answer "how does the system behave and how was it built/tested?"

## Current Status

For the current scope, the work is complete and validated.

The methodology goals that were achieved are:

- native LangGraph orchestration,
- native LangChain prompt/model boundary,
- Studio visibility,
- browser-assisted Studio inspection,
- rebuildable environment,
- repeatable API and CLI flows,
- tests that cover the most important edge cases discovered during real use.

## Next Hardening Steps

The next recommended technical improvements are:

1. move toward refs-only graph state,
2. add artifact schema versioning,
3. add evidence filtering/ranking before matching,
4. improve review UX beyond raw payload editing,
5. add explicit LangSmith metadata/tracing for job and round analysis.
