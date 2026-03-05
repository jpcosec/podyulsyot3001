# Prompt Pack (Non-ATS)

This directory contains the specification for every LLM prompt in the PhD 2.0 pipeline.

## Design principles

1. JSON = semantic state / machine contract.
2. Markdown = review surface or render content.
3. YAML = reusable active memory / config.
4. Every prompt is stage-aware and feedback-aware.
5. Downstream stages consume validated context, not raw job data.
6. The renderer is deterministic and non-creative.

## Prompt index

| # | Prompt | Owner node | Purpose |
|---|--------|-----------|---------|
| 1 | [Matcher](matcher.md) | `match` | Map job requirements to profile evidence |
| 2 | [Match Review Parser](match_review_parser.md) | `review_match` | Convert reviewed match proposal to validated state |
| 3 | [Application Context Builder](application_context_builder.md) | `build_application_context` | Create grounded shared context for downstream |
| 4 | [Motivation Letter Writer](motivation_letter_writer.md) | `generate_motivation_letter` | Draft evidence-grounded motivation letter |
| 5 | [Motivation Letter Review Parser](motivation_letter_review_parser.md) | `review_motivation_letter` | Convert reviewed letter to validated state |
| 6 | [CV Tailorer](cv_tailorer.md) | `tailor_cv` | Produce aligned CV content |
| 7 | [Email Drafter](email_drafter.md) | `draft_email` | Draft application email |
| 8 | [CV Review Parser](cv_review_parser.md) | `review_cv` | Convert reviewed CV draft to validated state |
| 9 | [Email Review Parser](email_review_parser.md) | `review_email` | Convert reviewed email draft to validated state |
| 10 | [CV Renderer](cv_renderer.md) | `render` | Deterministic CV compilation |
| 11 | [Feedback Distiller](feedback_distiller.md) | `feedback_distill` | Distill feedback into active memory |

## Artifact path conventions

All artifact paths in prompt specs use the rebuild's canonical layout:

- `nodes/<node>/proposed/state.json` (not `planning/` flat layout)
- `nodes/<node>/approved/state.json`
- `profile/profile_base_data.json`
- `feedback/active_memory.yaml`

See `docs/reference/artifact_schemas.md` for full schema definitions.

## Hard constraints (universal)

These constraints apply to every prompt:

- Do not invent evidence.
- Do not create claims not supported by approved upstream artifacts.
- Every proposed claim must cite evidence ids.
- Return only the requested output artifacts.
