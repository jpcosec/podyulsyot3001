# LangGraph Pipeline Migration — Overview

## Problem

The current pipeline is a flat list of step functions (`src/steps/*.py`) dispatched by the CLI. There's no execution graph — the data flow is implicit, mediated by filesystem conventions:

1. **`src/utils/pipeline.py` is a god file** — CVTailoringPipeline (3-agent chain), MatchProposalPipeline (single matcher + review loop), proposal parsing, and claim generation all live in one 650-line file
2. **Steps are isolated I/O functions** — each reads files, does work, writes files. No typed data passes between steps
3. **The review loop is hidden** — `match → human edit → regenerate` is encoded in a `force` flag, not as an explicit graph cycle
4. **Keyword extraction is bolted onto matching** — `_extract_keywords_from_proposal()` lives inside `matching.py` but is a separate concern
5. **CLI does coordination work** — `_next_workflow_verb()` and `_run_all_pending()` are business logic in the CLI layer
6. **Review quality is poor** — user notes in `<!-- comments -->` are dumped as a JSON blob instead of structured per-requirement directives, and `_propose_claim_text()` overwrites LLM output with a hardcoded template

## Solution

Introduce a LangGraph `StateGraph` as the pipeline coordinator:

```
START
  │
  ▼
ingest ──► match ──► keywords ──► review_gate ──┬──► motivate ──► email ──┐
              ▲                        │        │                         │
              └──── regenerate ────────┘        └──► tailor_cv ──► render ┤
                   (if edited)                     (subgraph)             ▼
                                                                      package
                                                                         │
                                                                         ▼
                                                                        END
```

- `review_gate` uses LangGraph `interrupt()` — pauses execution, user edits in Obsidian, resumes via CLI
- After resume: if any claim is `edited`, route back to `match`; if all approved/rejected, continue forward
- `tailor_cv` is a proper LangGraph subgraph (matcher → seller → checker)
- Review quality fix is woven into the migration from day one

## Implementation Phases

| Phase | Document | Summary |
|---|---|---|
| 0 | `01-scaffold.md` | Install LangGraph, create directory structure, state definition, stub graph |
| 1 | `02-extract-parsers-agents.md` | Extract parsers and agents from `pipeline.py` into focused modules |
| 2 | `03-core-nodes.md` | Implement ingest → match → keywords → review_gate with improved review quality |
| 3 | `04-remaining-nodes.md` | Implement motivate, email, tailor_cv (subgraph), render, package |
| 4 | `05-cli-checkpointing.md` | CLI integration with SQLite checkpointing, interrupt/resume UX |
| 5 | `06-cleanup-docs.md` | Deprecate old steps, update all docs, final changelog |

## Shared constraints (apply to ALL phases)

- **Migration-first, no `run` fallback after cutover** — tag the pre-cutover commit, then make `pipeline job <id> run` graph-only (no `run --legacy`)
- **Individual step verbs may remain** — keep `ingest`, `match`, etc. available for targeted/manual operations while graph execution is the primary path
- **Always persist artifacts to disk** — Obsidian integration depends on file-based artifacts in `data/pipelined_data/`
- **Reuse existing infrastructure** — `JobState`, `CVConfig`, `GeminiClient`, `src/render/`, `src/scraper/`, `src/models/` stay as-is
- **Each phase has its own commit** — with changelog and doc updates
- **Tests are mandatory** — no phase is complete without passing tests
- **Path resolution** — always use `Path(__file__).resolve().parents[n]`, never hardcode `/home/jp/phd`

### Non-negotiable refactorings

1. Split keyword extraction out of `src/steps/matching.py` into a dedicated keywords domain/module.
2. Split mixed domains in `src/utils/pipeline.py` (parsers, claim builder, agent orchestration) into focused modules under `src/graph/`.

## Key files reference

| File | Role | Modified? |
|---|---|---|
| `src/utils/pipeline.py` | God file being decomposed | Phase 1: extracted from, Phase 5: deprecated |
| `src/utils/state.py` | `JobState` — path authority | Unchanged |
| `src/utils/config.py` | `CVConfig` — project roots | Unchanged |
| `src/utils/gemini.py` | `GeminiClient` — LLM calls | Unchanged |
| `src/utils/comments.py` | Comment extraction | Unchanged |
| `src/models/pipeline_contract.py` | Pydantic models | Unchanged |
| `src/prompts/` | Agent prompt files | Unchanged |
| `src/render/` | DOCX/LaTeX/PDF rendering | Unchanged |
| `src/scraper/` | Scraping infrastructure | Unchanged |
| `src/steps/` | Current step functions | Phase 5: deprecated |
| `src/cli/pipeline.py` | CLI dispatcher | Phase 4: add graph commands |
| `environment.yml` | Conda deps | Phase 0: add langgraph |
