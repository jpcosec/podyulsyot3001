# Kept Code In-Depth Analysis

Date: 2026-03-02
Scope: analysis of all codepieces intentionally preserved for the rebuild

## 1) Gemini Caller Base

### File: `src/utils/gemini.py`

What it does:

- Provides a single `GeminiClient` to call Gemini text generation.
- Supports two SDK backends:
  - primary: `google.genai`
  - fallback: `google.generativeai`
- Loads env defaults from `.env` and optional `PHD_DOTENV_PATH`.

How it works:

1. `_load_gemini_sdk()` tries modern SDK, then legacy SDK.
2. `GeminiClient.__init__()` reads `GOOGLE_API_KEY`, chooses model (`GEMINI_MODEL` default `gemini-2.5-flash`), and initializes client.
3. `generate(prompt)` dispatches to selected SDK backend and returns plain `response.text`.

Why we keep it:

- It already centralizes API-key handling and model selection.
- It is reusable as the transport layer under the new LLM call template.

Current gaps (to be wrapped, not patched ad hoc in feature code):

- No retry policy or backoff strategy.
- No call counter / budget guard.
- No structured response parser.
- No telemetry events.

Rebuild role:

- Keep as low-level transport.
- New `llm/template.py` will sit above it and handle validation/retries/budgets.

## 2) Prompt Base

### Files: `src/prompts/*.txt`, `src/prompts/__init__.py`

What they do:

- Store domain prompt specifications as versioned text artifacts.
- `load_prompt(name)` provides file loading by name.
- `load_prompt_with_context(name, context_json)` injects `{{CONTEXT_JSON}}`.

Current prompt inventory:

- `cv_multi_agent.txt`: matcher/seller/checker behavior and schema intent.
- `cv_renderer.txt`: deterministic render instruction profile.
- `motivation_letter.txt`: letter generation contract.
- `email_draft.txt`: email generation contract.
- `ats_evaluation.txt`: ATS-style evaluator contract.

Why we keep them:

- They are the reusable policy layer for all LLM nodes.
- They keep behavior externalized and auditable.

Current gaps:

- Prompt files are not version-tagged in outputs.
- Runtime schema enforcement is currently fragmented in callers.

Rebuild role:

- Every LLM node uses the same prompt loading path.
- The new LLM template records prompt name/version fingerprint per call.

## 3) Pydantic Contract Base

### Files: `src/models/*.py`

Key contracts:

- `job.py`
  - `JobPosting`, `JobRequirement`
  - Normalized posting payload from deterministic extraction.
- `pipeline_contract.py`
  - `EvidenceItem`, `RequirementMapping`, `ProposedClaim`, `RenderConfig`, `PipelineState`
  - Existing claim/mapping backbone.
- `motivation.py`
  - `MotivationLetterOutput`, `EmailDraftOutput`, `FitSignal`
  - Generation outputs with strict fields.
- `application.py`
  - `FitAnalysis`, `ApplicationPlan`, `ApplicationBatch`
  - Batch planning artifacts.

Why we keep them:

- They are already close to the unified domain model.
- They provide strict contracts for graph node input/output validation.

Current gaps:

- Models are spread by legacy workflow boundaries.
- No single end-to-end state model for graph checkpoints.

Rebuild role:

- Keep existing models and add `ApplicationState` + per-node delta models.
- Keep strict `model_validate` as the mandatory parse boundary.

## 4) Deterministic Rendering Base

### Files: `src/render/docx.py`, `src/render/latex.py`, `src/render/pdf.py`, `src/render/styles.py`

What they do:

- `docx.py`
  - Deterministic DOCX rendering of CV sections.
  - ATS-safe constraints (single-column assumptions, explicit bullet rendering, controlled paragraph structure).
- `latex.py`
  - Deterministic template rendering via Jinja2.
  - Escapes special characters using `_latex_safe`.
- `pdf.py`
  - Deterministic text extraction path:
    - preferred `pdftotext`
    - fallback `pypdf`/`PyPDF2`
- `styles.py`
  - Controlled template style presets (`classic`, `modern`, `harvard`, `executive`).

Why we keep them:

- They are deterministic engines and independent from orchestration chaos.
- They already implement ATS-sensitive formatting decisions.

Current gaps:

- Render inputs are currently shaped by fragmented wrappers.
- No single render contract from unified proposal state.

Rebuild role:

- Preserve renderer APIs and wrap them in one `render_cv` graph node.

## 5) Deterministic Scrape + Translation Base

### Files: `src/scraper/scrape_single_url.py`, `src/scraper/deterministic_extraction.py`, `src/scraper/translate_markdowns.py`, `src/scraper/deep_translate_jobs.py`

What they do:

- `scrape_single_url.py`
  - URL-targeted deterministic ingestion.
  - Produces `raw/raw.html`, `raw/source_text.md`, `raw/language_check.json`, `raw/extracted.json`, `job.md`.
- `deterministic_extraction.py`
  - HTML parsing with deterministic section extraction and facts table parsing.
- `translate_markdowns.py`
  - Rules-based post-pass translation of selected markdown files.
- `deep_translate_jobs.py`
  - Optional machine translation pass using `deep-translator`.

Why we keep them:

- Ingestion should stay deterministic and auditable.
- Translation remains optional deterministic utility, not orchestration core.

Current gaps:

- Translation scripts are script-style (module-global loops), not reusable functions.
- Scope control is weak in script mode.

Rebuild role:

- Keep behavior but call through explicit graph node adapters with path guards.

## 6) Summary of Kept Assets

The rebuild keeps the strongest primitives:

- transport (`GeminiClient`)
- policies (`prompts`)
- contracts (`pydantic models`)
- deterministic outputs (`renderers`)
- deterministic ingestion (`scraper extraction + translation utilities`)

All orchestration, phase wiring, wrapper commands, and service glue are rebuilt around these bases.
