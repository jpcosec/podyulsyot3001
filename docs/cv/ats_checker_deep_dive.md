# ATS Checker Deep Dive

This document describes how ATS evaluation currently works in this repository, with implementation-level detail.

Scope:

- CV extraction targets (`docx` and `pdf`)
- scoring engines (deterministic code + LLM)
- parity checks between `to_render.md` and rendered artifacts
- operational commands and failure handling

## 1) Where ATS Runs in the Pipeline

Primary command path (CLI-first):

```bash
python src/cli/pipeline.py cv-validate-ats <job_id> --ats-target pdf
```

Shortcut command that builds + validates:

```bash
python src/cli/pipeline.py cv-pdf <job_id> <language> --via docx
```

Template parity quality gate:

```bash
python src/cli/pipeline.py cv-template-test <job_id> <language> --via docx --target docx --require-perfect
```

Direct module path (when needed):

```bash
python -m src.cv_generator validate-ats --job-id <job_id> --source tu_berlin --ats-target pdf
```

## 2) Output Contract

ATS reports are written to:

`data/pipelined_data/<source>/<job_id>/cv/ats/report.json`

The report is always JSON and includes engine-level status, final score, and parity diagnostics.

## 3) Execution Flow (Current Code Path)

Main orchestration:

- `src/cv_generator/__main__.py` (`validate_ats`)

Core ATS analysis:

- `src/cv_generator/ats.py` (`run_ats_analysis`)

Deterministic parity evaluator:

- `src/ats_tester/deterministic_evaluator.py`

Text extractors:

- `src/render/pdf.py` (`extract_docx_text`, `extract_pdf_text`)

Flow steps:

1. Resolve rendered artifact paths (`cv.docx`, `cv.pdf`).
2. Read job description (`job.md` by default, or override).
3. Extract text from selected ATS target (`--ats-target pdf|docx`).
4. Run dual-engine ATS scoring.
5. Compare `to_render.md` against rendered outputs.
6. Persist final report JSON.

## 4) Scoring Engines

### 4.1 Code engine

Default code engine path:

- `DeterministicContentEvaluator.analyze_cv(...)`
- delegates to `src/utils/nlp/text_analyzer.py`

If this fails (for example missing `spacy`), ATS falls back to:

- `fallback_ats_analysis(...)` in `src/cv_generator/ats.py`

### 4.2 LLM engine

LLM path:

- `src/utils/gemini.py` via `GeminiClient`

If unavailable (import/config errors), report marks the engine unavailable and includes a reason.

### 4.3 Combined score

Default weights:

- code: `0.6`
- llm: `0.4`

Modes:

- `fallback`: use available engines only
- `strict`: fail if any required engine is unavailable

## 5) Deterministic Parity Checker

Purpose:

- enforce that rendered CV text preserves `to_render.md` content and order

Input reference:

- `data/pipelined_data/<source>/<job_id>/cv/to_render.md`

Generation:

- `to_render.md` is auto-generated during CV `render`/`build` flows from the same canonical `CVModel` used by renderers.

Current behavior:

- if `to_render.md` is missing or empty (legacy/manual artifacts), parity is marked unavailable
- if present, compare against `cv.docx` (when it exists) and `cv.pdf` (when it exists)

Normalization logic (line-based):

- lowercase
- collapse whitespace
- keep only `[a-z0-9@+.#- ]`
- compare normalized lines in sequence

Metrics:

- `line_overlap_pct`
- `order_match_pct`
- `missing_lines` (truncated list)
- `out_of_order_lines` (truncated list)

Default thresholds:

- minimum overlap: `90.0`
- minimum order match: `85.0`

Pass condition:

- both thresholds must be met

## 6) Report Schema (Practical)

High-level keys in `report.json`:

- metadata: `id`, `analysis_date`, `ats_mode`, `ats_target`
- combined result: `score`, `summary`
- `engines.code` and `engines.llm`
- `content_parity`

Typical `content_parity` block:

```json
{
  "available": true,
  "docx": {
    "line_overlap_pct": 95.1,
    "order_match_pct": 91.0,
    "passed": true
  },
  "pdf": {
    "line_overlap_pct": 93.0,
    "order_match_pct": 88.7,
    "passed": true
  }
}
```

## 7) Operational Recommendations

Recommended ATS-first flow:

1. Build CV via DOCX engine to final PDF:
   - `python src/cli/pipeline.py cv-build <job_id> english --via docx --docx-template modern`
2. Run ATS on PDF:
   - `python src/cli/pipeline.py cv-validate-ats <job_id> --ats-target pdf`
3. Inspect report:
   - `data/pipelined_data/<source>/<job_id>/cv/ats/report.json`

Why this default:

- DOCX route is generally more ATS-friendly for text structure.
- Final acceptance target remains PDF, so ATS must be evaluated on extracted PDF text.

Template testing guidance:

- Use `--target docx --require-perfect` as the primary template quality gate.
- Use `--target pdf` to measure PDF extraction fidelity (informative; may be below 100% depending on converter/extraction behavior).

## 8) Failure Modes and Troubleshooting

### 8.1 `engines.code.used_fallback = true`

Likely cause:

- missing `spacy` runtime/model

Effect:

- system uses fallback heuristic analysis; score is less semantically precise

### 8.2 LLM engine unavailable

Likely cause:

- Gemini client import/config/auth issues

Effect:

- in `fallback` mode, scoring continues with code engine
- in `strict` mode, validation fails

### 8.3 `content_parity.available = false`

Likely causes:

- missing `to_render.md`
- no rendered artifacts found for comparison

Action:

- run current `render`/`build` flow first (it auto-generates `to_render.md`)

### 8.4 `--via docx` conversion failure

Likely cause:

- LibreOffice (`soffice`) not installed or not in `PATH`

Action:

- install LibreOffice CLI and retry

## 9) Known Limitations

1. Parity requires `to_render.md`; legacy/manual artifact sets may not contain it.
2. Fallback code analysis can inflate/deflate quality perception versus full deterministic analyzer.
3. PDF extraction quality depends on how the PDF was produced (font embedding/encoding/layout can affect text recovery).

## 10) Source Map

- ATS orchestration: `src/cv_generator/__main__.py`
- ATS engine composition: `src/cv_generator/ats.py`
- deterministic evaluator + parity thresholds: `src/ats_tester/deterministic_evaluator.py`
- text extraction helpers: `src/render/pdf.py`
- ATS formatting constraints and layout rules: `docs/cv/ats-guidelines.md`
