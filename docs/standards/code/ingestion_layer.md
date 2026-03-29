# 🔌 Ingestion Layer Standards

Standards for modules that sit at the system boundary — receiving uncontrolled external input and producing a validated internal representation. Extends `basic.md`.

Current ingestion components: `src/scraper/` (job portal crawling), `src/review_ui/` (human review input).
Planned: CV ingestion.

Scraper produces non-deterministic output (LLM-assisted extraction, portal variability) and is classified under LLM standards for its output contract. This document covers the **boundary concerns** that apply to all ingestion components regardless of whether the extraction step is deterministic or LLM-based.

---

## 1. The Ingestion Contract

Every ingestion component has exactly one job: receive external input, validate it, and produce a typed internal representation. It never does anything else.

```
External input (uncontrolled)
        ↓
  [Ingestion component]
        ↓
  Validated Pydantic model (internal contract)
```

The output model is the boundary. Downstream modules depend on the model, never on the raw external format.

---

## 2. Validation at the Boundary

All validation happens at ingestion time, not downstream.

- MANDATORY fields: missing or invalid → raise a domain-specific exception. Never allow a partial record to propagate.
- OPTIONAL fields: absent is valid. Document which fields are optional and what downstream behavior to expect when they're absent.
- Schema evolution: when the external format changes (new portal layout, new review payload shape), update the ingestion adapter — not the downstream contract.

```python
class IngestionValidationError(Exception): pass
class PartialExtractionError(Exception): pass  # LLM rescue produced incomplete output
```

---

## 3. Idempotency

Ingestion runs must be safe to re-run.

- If the output artifact already exists and is valid, skip and log `LogTag.SKIP`.
- Provide an explicit `--overwrite` / `--force` flag to re-ingest.
- Never silently overwrite existing validated artifacts.

```python
if output_path.exists() and not args.force:
    logger.info(f"{LogTag.SKIP} Already ingested: {output_path}")
    return
```

---

## 4. LLM Rescue Pattern

When extraction is primarily deterministic (CSS selectors, regex, structured parsing) but may fail on malformed input, an LLM rescue fallback is acceptable. Rules:

- The deterministic path is always attempted first.
- LLM rescue is only triggered on explicit failure, never speculatively.
- Log the rescue trigger explicitly with `LogTag.FALLBACK`.
- The rescue output must pass the same validation contract as the deterministic path.
- Cache the LLM-generated extraction schema after the first successful run — do not re-generate on every run.

```python
try:
    result = deterministic_extract(page)
    logger.info(f"{LogTag.FAST} CSS extraction succeeded")
except ExtractionError:
    logger.warning(f"{LogTag.FALLBACK} CSS extraction failed, invoking LLM rescue")
    result = llm_rescue_extract(page)

validated = OutputContract.model_validate(result)
```

---

## 5. Partial Output Handling

Ingestion may produce partial results (some records succeed, some fail). Handle explicitly:

- Write successful records.
- Log failures per-record with `LogTag.WARN` — include enough context to retry the specific record.
- Never abort the whole batch because one record failed.
- Write a `meta.json` alongside the output with: total attempted, succeeded, failed, failure reasons.

---

## 6. Human Review as an Ingestion Component

The review UI (`src/review_ui/`) is an ingestion component. It receives uncontrolled human input (button clicks, text fields, free-form notes) and produces a typed `ReviewPayload`.

Rules that apply:
- The same validation-at-boundary rule applies: validate `ReviewPayload` shape before passing it to the graph.
- Hash-check the source artifact the reviewer acted on — if the artifact changed since the UI loaded, reject the payload.
- A review submission with missing or invalid fields is a `IngestionValidationError`, not a graph error.

The graph should never receive a `ReviewPayload` it has to partially trust. Either it's valid and hash-checked, or it's rejected at the boundary.

---

## 7. Ingestion Component Structure

```
src/<module>/
  models.py       ← output Pydantic model (the internal contract)
  adapter.py      ← base adapter (abstract, defines the extraction contract)
  providers/      ← source-specific adapters
  main.py         ← CLI: discovery, dispatch, idempotency check
  storage.py      ← artifact paths, meta.json, idempotency state
```

For LLM-assisted ingestion, also:
```
  schema_cache/   ← cached LLM-generated extraction schemas (not committed)
```
