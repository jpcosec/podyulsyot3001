# Fix 1: Stop Filtering Data the LLM Needs

## The Problem

`scrape_single_url.py` produces two artifacts:
- `raw/source_text.md` — full markdown extraction of the HTML page
- `raw/extracted.json` — structured data filtered through section alias matching

Downstream steps (`cv_generator/pipeline.py`, motivation letter) only consume `extracted.json` and `job.md` (which is rendered from `extracted.json`). They never see `source_text.md`.

The alias matching in `collect_section_lines()` uses hardcoded section names:
```python
aliases=("your profile", "profile", "requirements", "anforderungen", "qualifikation")
```

Any section that doesn't match these aliases is silently dropped. This loses:
- Research group descriptions and project context
- "What we offer" sections (useful for motivation framing)
- Position descriptions that use non-standard headers
- Freeform text between sections
- Context about the department, lab, or PI

## The Fix

### Step 1: Preserve `source_text.md` as first-class artifact

`source_text.md` already exists in `raw/`. The fix is making downstream steps aware of it.

Add a `source_text` field to the job tracker frontmatter in `job.md`:
```yaml
source_text_path: raw/source_text.md
```

No scraper code changes needed for this — just update `render_tracker_markdown()` to include the path.

### Step 2: Add `raw/source_text.md` content to the pipeline context

In `CVTailoringPipeline._build_initial_context()`, add the full source text:

```python
# Current: only job.md requirements + profile
context = {"job": job.model_dump(), "profile": profile, "candidate": {...}}

# New: add full job description
source_text_path = job_dir / "raw" / "source_text.md"
if source_text_path.exists():
    context["full_job_description"] = source_text_path.read_text()
```

Same for motivation letter context assembly.

### Step 3: Keep deterministic extraction as metadata, not as the primary source

`extracted.json` still gets produced — it's useful for structured fields (deadline, reference number, contact email). But the LLM steps receive `source_text.md` as the authoritative job description.

`job.md` remains the human-editable tracker with checklists. It is not the LLM's primary source anymore.

## Files Changed

| File | Change |
|------|--------|
| `src/scraper/scrape_single_url.py` | Add `source_text_path` to tracker frontmatter |
| `src/cv_generator/pipeline.py` | Load and pass `source_text.md` in context |
| `src/cli/pipeline.py` | Pass `source_text.md` to motivation letter context |

## What NOT to change

- The scraper extraction logic itself — it still produces `extracted.json` for structured fields
- The `job.md` format — it remains the human-facing tracker
- The HTML download or markdown conversion — those work fine

## Testing

1. Re-scrape job 201084 and verify `source_text.md` content is complete
2. Run `cv-tailor` with the new context and verify the LLM receives full job text
3. Compare matching quality: old (extracted.json only) vs new (full source_text.md)
