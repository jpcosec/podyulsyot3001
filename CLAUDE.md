# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Postulator 3000 is a modular job application pipeline that produces tailored CV and motivation letter documents from job postings. It combines a scraper, translator, LangGraph-native matching engine (with HITL review via a Textual TUI), document generation, and a typed render pipeline.

## Commands

```bash
# Run all tests
python -m pytest tests/ -q

# Run a single test file
python -m pytest tests/test_match_skill.py -q

# Scrape job postings
python -m src.ai.scraper.main --source stepstone --limit 5

# Translate scraped postings
python -m src.tools.translator.main --source stepstone

# Run match skill (start a new thread)
python -m src.ai.match_skill.main \
  --source stepstone \
  --job-id <ID> \
  --requirements <path/to/requirements.json> \
  --profile-evidence <path/to/evidence.json>

# Launch HITL review TUI (after graph pauses at breakpoint)
python -m src.cli.main review --source stepstone --job-id <ID>

# Render CV to PDF
python -m src.tools.render.main cv \
  --source stepstone \
  --job-id <ID> \
  --language en

# Render motivation letter
python -m src.tools.render.main letter --source <path/to/data.json> --language de
```

## Architecture

### Module layout

Each skill is a self-contained package under `src/`:

- `src/ai/match_skill/` — LangGraph-native matching loop: `graph.py` (StateGraph), `contracts.py` (Pydantic I/O), `storage.py` (artifact persistence), `prompt.py`, `main.py`.
- `src/ai/generate_documents/` — LangGraph document generation nodes: same structure as match_skill.
- `src/tools/render/` — typed, engine-agnostic PDF/DOCX rendering via Pandoc + Jinja2. Entry point is `RenderCoordinator` in `coordinator.py`; `RenderRequest` in `request.py` is the unified request model.
- `src/ai/scraper/` — anti-bot job crawling with LLM fallbacks. Outputs `JobPosting` Pydantic models.
- `src/tools/translator/` — field and document translation pipeline.
- `src/review_ui/` — Textual TUI: `app.py` (`MatchReviewApp`), `bus.py` (`MatchBus` connects UI to LangGraph + disk), `screens/`, `widgets/`.

### Control plane vs. data plane

**Control plane** (`MatchSkillState` TypedDict in `src/ai/match_skill/graph.py`): carries routing signals and refs — `source`, `job_id`, requirements, profile evidence, review payload, match result. State is intentionally thin; heavy payloads stay on disk.

**Data plane** (disk under `data/jobs/<source>/<job_id>/nodes/match_skill/`): `MatchArtifactStore` in `storage.py` manages immutable round snapshots (JSON), current review surface, and approved payloads.

### Match skill graph flow

`match_node → [interrupt_before review] → review_node`

Review node routes via `Command`: `approve` (continue), `request_regeneration` (loop back to `match_node`), `reject` (end). Checkpointed with `SqliteSaver` (prod) or `InMemorySaver` (tests). `thread_id` is the LangGraph handle for resume.

### Render pipeline

`RenderRequest` → `RenderCoordinator` → resolves document adapter + style manifest + language bundle → `LatexRenderer` (Pandoc) → output file. Document types (`cv`, `letter`) and engines (`tex`, `docx`) are registered in `src/tools/render/registry.py`.

### HITL review loop

1. `run_match_skill` starts a thread; graph pauses at the review breakpoint.
2. Operator launches the `review` CLI command with the thread ID context.
3. `MatchBus` loads the review surface from `MatchArtifactStore` and holds the paused graph handle.
4. Reviewer approves/rejects/requests regeneration in the TUI; `MatchBus` resumes the thread via `Command`.
5. Immutable round snapshots are written to disk after each decision.

### Shared data contracts

- `JobPosting` — standardized job schema across scrapers and translators.
- `MatchEnvelope` / `RequirementMatch` — LLM structured output for match decisions.
- `ReviewSurface` / `ReviewPayload` — the JSON artifact exchanged between graph, TUI, and storage.
- `RenderRequest` — unified input model for the render coordinator.

### Failure model

Nodes must fail closed — no silent fallback-to-success. LLM calls use structured output (LangChain `with_structured_output`). Missing credentials fall back to a demo chain in dev only (explicit `os.environ.get` guard in `src/ai/generate_documents/graph.py`).

## Key documentation

- LangGraph component standards: `docs/standards/code/llm_langgraph_components.md`
- LangGraph methodology: `docs/standards/code/llm_langgraph_methodology.md`
- Match skill hardening roadmap: `future_docs/issues/match_skill_hardening_roadmap.md`
- Documentation & planning guide: `docs/standards/docs/documentation_and_planning_guide.md`

## Environment

```env
GOOGLE_API_KEY=...       # Gemini API access
GEMINI_API_KEY=...       # same key, both names accepted
PLAYWRIGHT_BROWSERS_PATH=0  # for scraper browser automation
```

Requires: `pandoc` and `texlive-full` (or equivalent) installed for PDF rendering.
