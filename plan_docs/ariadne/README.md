# Ariadne — Path Knowledge System

Date: 2026-04-05
Status: design-only, no code exists (proto-models exist in `src/apply/browseros_models.py`)

## What Ariadne is

Ariadne is the backend-neutral source of truth for path knowledge. It defines a
common language that all motors translate to and from, stores normalized paths,
and manages their lifecycle from raw recording to production-ready replay artifact.

Ariadne is not a motor. It never acts on pages and never observes them directly.
Motors act and observe; Ariadne knows.

## What Ariadne owns

| Concern | Document |
|---|---|
| Common language models (steps, actions, targets) | [common_language.md](common_language.md) |
| Recording pipeline (intake from agent/human motors) | [recording_pipeline.md](recording_pipeline.md) |
| Deterministic translators (common language → motor format) | [translators.md](translators.md) |
| Disk storage, versioning, path naming | [storage.md](storage.md) |
| Path promotion lifecycle (draft → verified → canonical) | [promotion.md](promotion.md) |
| Backend-neutral error taxonomy | [error_taxonomy.md](error_taxonomy.md) |

## How Ariadne fits in the architecture

```
Motors (act)                    Ariadne (knows)
────────────                    ───────────────
Crawl4AI          ──consumes──▶ paths (via translator)
BrowserOS CLI     ──consumes──▶ paths (via translator)
BrowserOS Agent   ──produces──▶ recording pipeline ──▶ storage
Human             ──produces──▶ recording pipeline ──▶ storage
OS Native         ──consumes──▶ paths (via translator)
Vision            ──consumes──▶ paths (target resolution)
```

**Intake side**: the BrowserOS Agent motor and Human motor produce raw session
events. The recording pipeline normalizes them into common language and stores
them as draft paths.

**Output side**: when a motor needs to replay a path, the translator compiles
common-language steps into the motor's native format. Translation is deterministic
— no LLM, no runtime inference.

**Portals** supply the domain knowledge that populates AriadneTarget fields
(CSS selectors, text labels, image templates) for each portal's flows.

## What exists today (proto-Ariadne)

The current `src/apply/browseros_models.py` is a proto-Ariadne common language,
but it's BrowserOS-coupled:

- `BrowserOSPlaybook` → future `AriadnePath`
- `PlaybookStep` → future `AriadneStep`
- `PlaybookAction` → future `AriadneAction`
- `ObserveBlock` → future observe semantics in `AriadneStep`
- `PlaybookMeta` / `PlaybookEntryPoint` → future path metadata

One packaged playbook exists: `src/apply/playbooks/linkedin_easy_apply_v1.json`
(LinkedIn Easy Apply, 5 steps, dry-run verified).

The refactoring task is to generalize these models into the common language,
removing BrowserOS-specific tool names and adding multi-strategy target resolution.

## Design decisions already made

These are documented in `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md`:

1. **Multi-strategy AriadneTarget** with per-backend fields (css, text, image_template,
   ocr_text, region) — each motor uses what it understands
2. **Target precedence order**: CSS → Text → OCR → Image template (within a single backend)
3. **Crawl4AI translator is a compiler** (compiles step lists into C4A-Script strings)
4. **Intent vocabulary** instead of backend tool names (fill_react_controlled, not evaluate_script_react)
5. **Normalize on capture** (Option A) — recordings convert to common language immediately
6. **Fallbacks in common language** — not motor-specific
7. **human_required and dry_run_stop in common step model** — cross-backend concerns
8. **Vision target fields reserved now** — even though vision motor is a stub
