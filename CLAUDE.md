# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Postulator 3000 is a modular job application pipeline that produces tailored CV and motivation letter documents from job postings. It combines a scraper, translator, LangGraph-native matching engine (with HITL review via a Textual TUI), document generation, and a typed render pipeline.

## Commands

```bash
# Run all tests
python -m pytest tests/ -q

# Run a focused test subtree
python -m pytest tests/unit/core/ai/generate_documents_v2 -q

# Scrape job postings
python -m src.scraper.main --source stepstone --limit 5

# Translate scraped postings
python -m src.core.tools.translator.main --source stepstone

# Run document generation pipeline helpers
python -m src.cli.main generate --source stepstone --job-id <ID> --language en --render

# Launch HITL review TUI (after graph pauses at breakpoint)
python -m src.cli.main review --source stepstone --job-id <ID>

# Render CV to PDF
python -m src.core.tools.render.main cv \
  --source stepstone \
  --job-id <ID> \
  --language en

# Render motivation letter
python -m src.core.tools.render.main letter --source <path/to/data.json> --language de
```

## Architecture

### Module layout

Each skill is a self-contained package under `src/`:

- `src/core/ai/generate_documents_v2/` — LangGraph-native staged document generation: `graph.py`, `contracts/`, `storage.py`, `nodes/`, `subgraphs/`, `pipeline.py`.
- `src/core/tools/render/` — typed, engine-agnostic PDF/DOCX rendering via Pandoc + Jinja2. Entry point is `RenderCoordinator` in `coordinator.py`; `RenderRequest` in `request.py` is the unified request model.
- `src/scraper/` — anti-bot job crawling with LLM fallbacks. Outputs `JobPosting` Pydantic models.
- `src/core/tools/translator/` — field and document translation pipeline.
- `src/review_ui/` — Textual TUI: `app.py` (`MatchReviewApp`), `bus.py` (`MatchBus` connects UI to LangGraph + disk), `screens/`, `widgets/`.

### Control plane vs. data plane

**Control plane** lives in the operator CLI and API-backed review flow; it carries routing signals, job identifiers, and lightweight review metadata.

**Data plane** lives under `data/jobs/<source>/<job_id>/nodes/`, where module artifacts are persisted by `DataManager` and module-local storage helpers.

### Document generation graph flow

`ingestion → requirement_filter → alignment → blueprint → drafting → assembly`

The graph persists stage artifacts per step and can expose review-oriented artifacts without duplicating the heavy payload in control-plane state.

### Render pipeline

`RenderRequest` → `RenderCoordinator` → resolves document adapter + style manifest + language bundle → `LatexRenderer` (Pandoc) → output file. Document types (`cv`, `letter`) and engines (`tex`, `docx`) are registered in `src/core/tools/render/registry.py`.

### HITL review loop

1. Operator launches runs through `src/cli/main.py`.
2. Review surfaces are loaded in `src/review_ui/` from canonical artifacts and API metadata.
3. Reviewer acts through the TUI and the control plane resumes or updates the relevant workflow.

### Shared data contracts

- `JobPosting` — standardized job schema across scrapers and translators.
- `JobKG` / `JobDelta` — staged job-understanding contracts for document generation.
- `RenderRequest` — unified input model for the render coordinator.

### Failure model

Nodes must fail closed — no silent fallback-to-success. LLM calls use structured output (LangChain `with_structured_output`). Missing credentials fall back to a demo chain in dev only where explicitly implemented, for example in `src/core/ai/generate_documents_v2/graph.py`.

## Key documentation

- LangGraph component standards: `docs/standards/code/llm_langgraph_components.md`
- LangGraph methodology: `docs/standards/code/llm_langgraph_methodology.md`
- Documentation & planning guide: `docs/standards/docs/documentation_and_planning_guide.md`

## Environment

```env
GOOGLE_API_KEY=...       # Gemini API access
GEMINI_API_KEY=...       # same key, both names accepted
PLAYWRIGHT_BROWSERS_PATH=0  # for scraper browser automation
```

Requires: `pandoc` and `texlive-full` (or equivalent) installed for PDF rendering.
