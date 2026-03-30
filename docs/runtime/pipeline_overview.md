# Pipeline Overview

Navigation index for the Postulator 3000 pipeline. Each module has its own README as the authoritative source. This document explains how the modules relate and where cross-cutting design decisions are documented.

---

## Module Map

| Module | Type | README | Purpose |
|--------|------|--------|---------|
| `src/scraper/` | Deterministic + LLM fallback | `src/scraper/README.md` | Discover and ingest job postings → `JobPosting` |
| `src/core/tools/translator/` | Deterministic | `src/core/tools/translator/README.md` | Translate scraped JSON fields + Markdown body |
| `src/core/ai/match_skill/` | LangGraph | `src/core/ai/match_skill/README.md` | Requirement-to-evidence matching with HITL review |
| `src/review_ui/` | Textual TUI | `src/review_ui/README.md` | Terminal interface for the match review gate |
| `src/core/ai/generate_documents/` | LangGraph | `src/core/ai/generate_documents/README.md` | CV, letter, and email generation from approved matches |
| `src/core/tools/render/` | Deterministic | `src/core/tools/render/README.md` | Pandoc + Jinja2 → PDF / DOCX |
| `src/shared/` | Library | `src/shared/README.md` | Cross-cutting utilities (log tags) |
| `src/core/ai/match_skill/main.py` | CLI entry point | `src/core/ai/match_skill/README.md` | Run or resume the match skill pipeline |

---

## Pipeline Sequence

```
src/scraper/
  ↓  canonical raw job artifacts under `nodes/ingest/proposed/`
src/core/tools/translator/
  ↓  translated fields + content.md
src/core/ai/match_skill/          ← LangGraph, pauses for HITL review
  ↑  review decisions via src/review_ui/ (Textual TUI)
  ↓  approved/state.json
src/core/ai/generate_documents/   ← LangGraph
  ↓  cv.md, cover_letter.md, email_body.txt
src/core/tools/render/
  ↓  PDF / DOCX artifacts
```

Schema-v0 runtime rules for artifact placement, job metadata, and the central data manager are defined in `docs/runtime/data_management.md`.

---

## Cross-Cutting Design Decisions

### Control plane vs. data plane

All LangGraph state (`MatchSkillState`) carries only routing signals — source, job_id, refs, and decision flags. Heavy payloads (match proposals, generated documents) stay on disk. This keeps checkpointed state small and makes artifacts inspectable without replaying the graph.

### Node execution model

For the schema-v0 top-level pipeline in `src/graph/`, nodes run synchronously by default. The surrounding CLI, scraper, API client, and TUI may still use async where network interaction requires it, but graph-node bodies themselves should stay sync unless a node is genuinely async end-to-end.

### Artifact layout

```text
data/jobs/<source>/<job_id>/
  meta.json
  nodes/<node>/<stage>/<artifact>
```

See `docs/runtime/data_management.md` for the schema-v0 canonical layout.

### Failure model

All nodes fail closed — no silent fallback-to-success. LLM calls use `with_structured_output`. Missing credentials fall back to a demo chain in dev only (explicit guard in `src/core/ai/generate_documents/graph.py`).

### Observability

All log lines use `LogTag` from `src/shared/log_tags.py`. Never write emoji strings by hand. See `docs/standards/docs/documentation_and_planning_guide.md` §3 for the full tag vocabulary.

---

## Further Reading

- Match skill hardening roadmap: `future_docs/issues/match_skill_hardening_roadmap.md`
- LangGraph component standards: `docs/standards/code/llm_langgraph_components.md`
- Documentation conventions: `docs/standards/docs/documentation_and_planning_guide.md`
- Old pipeline → new module mapping: `src/PIPELINE_MAPPING.md`
- Schema-v0 data plane: `docs/runtime/data_management.md`
