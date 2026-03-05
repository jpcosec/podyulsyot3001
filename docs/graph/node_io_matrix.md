# Node I/O Matrix

## Purpose

This matrix defines the final-state I/O contract expectations for each graph node.

It complements:

- `docs/graph/graph_definition.md` (flow and routing semantics)
- `docs/philosophy/structure_and_rationale.md` (architectural boundaries)

JSON artifacts are canonical. Markdown artifacts are human-facing review surfaces.

## Legend

- Execution class:
  - `LLM` = step uses an LLM.
  - `NLLM-D` = non-LLM deterministic step.
  - `NLLM-ND` = non-LLM bounded-nondeterministic step.
- Review gate: whether the node requires an explicit HITL review decision before flow continues.
- Paths are shown relative to `data/jobs/<source>/<job_id>/`.

## Matrix

| Node | Execution Class | Required Inputs | Proposed Outputs | Review Gate | Approved Outputs | Downstream Consumers | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `scraping` (pre-graph) | `NLLM-ND` | External URL/listing source | `raw/raw.html`, `raw/source_text.md`, `raw/extracted.json`, `raw/language_check.json` | No | N/A | `ingest` | Source prep stage before graph run; network-dependent variability is expected. |
| `ingest` | `NLLM-D` | `raw/*` source artifacts | `nodes/ingest/proposed/state.json` | No | `nodes/ingest/approved/state.json` | `extract_understand` | Normalizes source presence and baseline metadata. |
| `extract_understand` | `NLLM-D` | `nodes/ingest/approved/state.json`, `raw/extracted.json`, `raw/source_text.md` | `nodes/extract_understand/proposed/state.json` | No | `nodes/extract_understand/approved/state.json` | `translate` | Produces structured understanding (requirements/themes/responsibilities/constraints). |
| `translate` | `NLLM-ND` | `nodes/extract_understand/approved/state.json` | `nodes/translate/proposed/state.json` | No | `nodes/translate/approved/state.json` | `match` | No LLM; variability comes from external translation backend behavior. |
| `match` | `LLM` | `nodes/translate/approved/state.json`, profile context | `nodes/match/proposed/state.json`, `nodes/match/proposed/view.md`, `nodes/match/review/decision.md` | Yes (`review_match`) | N/A (approval happens in review node) | `review_match` | Must not silently fallback to fake success. |
| `review_match` | `NLLM-D` | `nodes/match/proposed/state.json`, `nodes/match/review/decision.md` | `nodes/match/review/decision.json` | Decision parser | `nodes/review_match/approved/state.json`, `nodes/review_match/meta/provenance.json` | `build_application_context` or loop/stop | Enforces decision validity and stale-hash protection. |
| `build_application_context` | `LLM` | `nodes/review_match/approved/state.json`, profile constraints | `nodes/build_application_context/proposed/state.json`, `nodes/build_application_context/proposed/view.md`, `nodes/build_application_context/review/decision.md` | Yes (`review_application_context`) | N/A (approval happens in review node) | `review_application_context` | Creates grounded strategy/context from approved mapping. |
| `review_application_context` | `NLLM-D` | `nodes/build_application_context/proposed/state.json`, `nodes/build_application_context/review/decision.md` | `nodes/build_application_context/review/decision.json` | Decision parser | `nodes/review_application_context/approved/state.json`, `nodes/review_application_context/meta/provenance.json` | `generate_motivation_letter`, `tailor_cv`, `draft_email` | Must preserve reviewed decisions deterministically. |
| `generate_motivation_letter` | `LLM` | `nodes/review_application_context/approved/state.json` | `nodes/generate_motivation_letter/proposed/state.json`, `nodes/generate_motivation_letter/proposed/letter.md`, `nodes/generate_motivation_letter/proposed/view.md`, `nodes/generate_motivation_letter/review/decision.md` | Yes (`review_motivation_letter`) | N/A (approval happens in review node) | `review_motivation_letter` | Must reference approved claims only. |
| `review_motivation_letter` | `NLLM-D` | `nodes/generate_motivation_letter/proposed/state.json`, `nodes/generate_motivation_letter/review/decision.md` | `nodes/generate_motivation_letter/review/decision.json` | Decision parser | `nodes/review_motivation_letter/approved/state.json`, `nodes/review_motivation_letter/meta/provenance.json` | `tailor_cv`, `draft_email`, `render` | Applies review decisions and records provenance. |
| `tailor_cv` | `LLM` | `nodes/review_application_context/approved/state.json`, `nodes/review_motivation_letter/approved/state.json` | `nodes/tailor_cv/proposed/state.json`, `nodes/tailor_cv/proposed/to_render.md`, `nodes/tailor_cv/proposed/view.md`, `nodes/tailor_cv/review/decision.md` | Yes (`review_cv`) | N/A (approval happens in review node) | `review_cv` | Produces CV proposal that must pass explicit review. |
| `review_cv` | `NLLM-D` | `nodes/tailor_cv/proposed/state.json`, `nodes/tailor_cv/proposed/to_render.md`, `nodes/tailor_cv/review/decision.md` | `nodes/tailor_cv/review/decision.json` | Decision parser | `nodes/review_cv/approved/state.json`, `nodes/review_cv/approved/to_render.md`, `nodes/review_cv/meta/provenance.json` | `draft_email`, `review_email`, `render` | Enforces CV pass/regenerate/reject decisions. |
| `draft_email` | `LLM` | `nodes/review_application_context/approved/state.json`, `nodes/review_motivation_letter/approved/state.json`, `nodes/review_cv/approved/state.json` | `nodes/draft_email/proposed/state.json`, `nodes/draft_email/proposed/application_email.md`, `nodes/draft_email/proposed/view.md`, `nodes/draft_email/review/decision.md` | Yes (`review_email`) | N/A (approval happens in review node) | `review_email` | Must be job-specific, no generic template fallback. |
| `review_email` | `NLLM-D` | `nodes/draft_email/proposed/state.json`, `nodes/draft_email/proposed/application_email.md`, `nodes/draft_email/review/decision.md` | `nodes/draft_email/review/decision.json` | Decision parser | `nodes/review_email/approved/state.json`, `nodes/review_email/approved/application_email.md`, `nodes/review_email/meta/provenance.json` | `render`, delivery | Enforces email pass/regenerate/reject decisions. |
| `render` | `NLLM-D` | `nodes/review_cv/approved/to_render.md`, `nodes/review_motivation_letter/approved/state.json`, `nodes/review_email/approved/state.json` | `nodes/render/proposed/state.json` | No | `nodes/render/approved/state.json`, `nodes/render/meta/provenance.json`, `final/cv.pdf|md`, `final/motivation_letter.pdf|md` | `package` | Final renderer can target DOCX/PDF and retain metadata. |
| `package` | `NLLM-D` | Render outputs from `final/` | `nodes/package/proposed/state.json` | No | `nodes/package/approved/state.json`, `nodes/package/meta/provenance.json`, `final/Final_Application.pdf|md`, `final/manifest.json` | End of graph | Must include hash manifest and reproducible package metadata. |

## Review-gated routing rules

For `review_match`, `review_application_context`, `review_motivation_letter`, `review_cv`, and `review_email`:

- `approve` -> continue to next stage.
- `request_regeneration` -> return to corresponding generator node.
- `reject` -> terminate run.

## Non-negotiable checks per node completion

1. Required canonical files exist.
2. Output JSON validates against node contract schema.
3. Review nodes reject malformed or stale decisions.
4. Approved artifacts carry provenance where required.
5. Downstream reads only from `approved/` paths.
