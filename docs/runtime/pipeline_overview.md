# Pipeline Overview

Navigation index for the Postulator 3000 pipeline. Each module has its own README as the authoritative source. This document explains how the modules relate and where cross-cutting design decisions are documented.

---

## Module Map

| Module | Type | README | Purpose |
|--------|------|--------|---------|
| `src/ai/scraper/` | Deterministic + LLM fallback | `src/ai/scraper/README.md` | Crawl job portals → `JobPosting` |
| `src/tools/translator/` | Deterministic | `src/tools/translator/README.md` | Translate scraped JSON fields + Markdown body |
| `src/ai/match_skill/` | LangGraph | `src/ai/match_skill/README.md` | Requirement-to-evidence matching with HITL review |
| `src/review_ui/` | Textual TUI | `src/review_ui/README.md` | Terminal interface for the match review gate |
| `src/ai/generate_documents/` | LangGraph | `src/ai/generate_documents/README.md` | CV, letter, and email generation from approved matches |
| `src/tools/render/` | Deterministic | `src/tools/render/README.md` | Pandoc + Jinja2 → PDF / DOCX |
| `src/shared/` | Library | `src/shared/README.md` | Cross-cutting utilities (log tags) |
| `src/ai/match_skill/main.py` | CLI entry point | `src/ai/match_skill/README.md` | Run or resume the match skill pipeline |

---

## Pipeline Sequence

```
src/ai/scraper/
  ↓  JobPosting (JSON)
src/tools/translator/
  ↓  translated fields + content.md
src/ai/match_skill/          ← LangGraph, pauses for HITL review
  ↑  review decisions via src/review_ui/ (Textual TUI)
  ↓  approved/state.json
src/ai/generate_documents/   ← LangGraph
  ↓  cv.md, cover_letter.md, email_body.txt
src/tools/render/
  ↓  PDF / DOCX artifacts
```

The relationship between `match_skill` and `generate_documents` (embedded node vs. standalone graph) is an open architectural question tracked in `future_docs/issues/orchestration.md`.

---

## Cross-Cutting Design Decisions

### Control plane vs. data plane

All LangGraph state (`MatchSkillState`) carries only routing signals — source, job_id, refs, and decision flags. Heavy payloads (match proposals, generated documents) stay on disk. This keeps checkpointed state small and makes artifacts inspectable without replaying the graph.

### Artifact layout

```
output/match_skill/<source>/<job_id>/
  nodes/match_skill/
    approved/state.json
    review/current.json
    review/rounds/round_<NNN>/
  nodes/generate_documents/
    deltas.json
    cv.md
    cover_letter.md
    email_body.txt
```

### Failure model

All nodes fail closed — no silent fallback-to-success. LLM calls use `with_structured_output`. Missing credentials fall back to a demo chain in dev only (explicit guard in `generate_documents/graph.py`).

### Observability

All log lines use `LogTag` from `src/shared/log_tags.py`. Never write emoji strings by hand. See `docs/standards/docs/documentation_and_planning_guide.md` §3 for the full tag vocabulary.

---

## Further Reading

- Match skill product guide (HITL design, graph topology, Studio exposure): `docs/runtime/match_skill_product_guide.md`
- Match skill implementation retrospective: `docs/runtime/match_skill_implementation_methodology.md`
- Documentation conventions: `docs/standards/docs/documentation_and_planning_guide.md`
- Old pipeline → new module mapping: `src/PIPELINE_MAPPING.md`
- Open architectural issues: `future_docs/issues/`
