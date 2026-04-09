# Pipeline Overview

Navigation index for the Postulator 3000 pipeline. Each module has its own README as the authoritative source. This document explains how the modules relate and where cross-cutting design decisions are documented.

---

## Module Map

| Module | Type | README | Purpose |
|--------|------|--------|---------|
| `src/scraper/` | Deterministic + LLM fallback | `src/scraper/README.md` | Discover and ingest job postings → `JobPosting` |
| `src/core/tools/translator/` | Deterministic | `src/core/tools/translator/README.md` | Translate scraped JSON fields + Markdown body |
| `src/review_ui/` | Textual TUI | `src/review_ui/README.md` | Operator review surfaces and workflow UI |
| `src/core/ai/generate_documents_v2/` | LangGraph | `src/core/ai/generate_documents_v2/README.md` | Multi-stage CV, letter, and email generation pipeline |
| `src/core/tools/render/` | Deterministic | `src/core/tools/render/README.md` | Pandoc + Jinja2 → PDF / DOCX |
| `src/shared/` | Library | `src/shared/README.md` | Cross-cutting utilities (log tags) |

---

## Pipeline Sequence

```
src/scraper/
  ↓  canonical raw job artifacts under `nodes/ingest/proposed/`
src/core/tools/translator/
  ↓  translated fields + content.md
src/core/ai/generate_documents_v2/   ← LangGraph with HITL checkpoints
  ↓  persisted reviewable artifacts + pending review states
src/review_ui/                    ← operator review/explorer surfaces over LangGraph threads
  ↓  approve/reject decisions and profile-writeback approval
src/core/ai/generate_documents_v2/
  ↓  cv.md, cover_letter.md, email_body.txt
src/core/tools/render/
  ↓  PDF / DOCX artifacts
```

Schema-v0 runtime rules for artifact placement, job metadata, and the central data manager are defined in `docs/runtime/data_management.md`.

---

## Cross-Cutting Design Decisions

### Control plane vs. data plane

All LangGraph state (`GenerateDocumentsV2State`) carries only routing signals, lightweight payload refs, and decision flags. Heavy artifacts (match surfaces, blueprints, drafts, Markdown bundles) stay on disk. This keeps checkpointed state small and makes artifacts inspectable without replaying the graph.

### Node execution model

For the current schema-v0 runtime, deterministic node and helper logic should stay synchronous by default. The surrounding CLI, scraper, API client, and TUI may still use async where network interaction requires it, but graph-node bodies themselves should stay sync unless a node is genuinely async end-to-end.

### Artifact layout

```text
data/jobs/<source>/<job_id>/
  meta.json
  nodes/<node>/<stage>/<artifact>
```

See `docs/runtime/data_management.md` for the schema-v0 canonical layout.

### Failure model

All nodes fail closed — no silent fallback-to-success. LLM calls use `with_structured_output`. Operator-facing CLI flows should surface remote failures explicitly instead of reporting success with unknown status.

### Observability

All log lines use `LogTag` from `src/shared/log_tags.py`. Never write emoji strings by hand. See `docs/standards/docs/documentation_and_planning_guide.md` §3 for the full tag vocabulary.

---

## Further Reading

- LangGraph component standards: `docs/standards/code/llm_langgraph_components.md`
- Documentation conventions: `docs/standards/docs/documentation_and_planning_guide.md`
- Old pipeline → new module mapping: `src/PIPELINE_MAPPING.md`
- Schema-v0 data plane: `docs/runtime/data_management.md`
