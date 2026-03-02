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

Additionally, `job.md` currently only contains filtered checklists. The user needs to read the **full** job posting in English to decide whether to apply.

## The Fix

### Step 1: `job.md` becomes the full translated job posting

`job.md` must contain the **entire job posting text, translated to English**. This is the human-facing document used to decide if a job is worth applying to. It keeps its YAML frontmatter (deadline, reference number, contact, etc.) but the body is the complete posting — not filtered checklists.

New `render_tracker_markdown()` output structure:
```markdown
---
status: Open
deadline: 20.03.2026
reference_number: III-51/26
university: TU Berlin
contact_person: Prof. Example
contact_email: example@tu-berlin.de
url: https://...
---

# Research Assistant III-51/26, Bioprocess Engineering

[Full job posting text here — every section, translated to English]
```

The existing translation step (`translate_markdowns.py` or `deep_translate_jobs.py`) already handles German→English. The change is: translate the **full** `source_text.md` content into `job.md`, not just the filtered sections.

### Step 2: Keep `extracted.json` as structured metadata only

`extracted.json` still gets produced — it's useful for programmatic access to deadline, reference number, contact email. But it is no longer the primary source for anything. It's metadata.

### Step 3: Pass `job.md` (full text) to LLM steps

Since `job.md` now contains the complete translated posting, LLM steps can just read it directly. No need for a separate `source_text.md` pass — `job.md` IS the full text, in English.

In `CVTailoringPipeline._build_initial_context()`:
```python
# job.md already contains the full translated posting
context["full_job_description"] = job_md_path.read_text()
```

Same for motivation letter context assembly.

## Files Changed

| File | Change |
|------|--------|
| `src/scraper/scrape_single_url.py` | `render_tracker_markdown()` outputs full text body instead of filtered checklists |
| `src/cv_generator/pipeline.py` | `_build_initial_context()` passes full job.md content |
| `src/cli/pipeline.py` | Motivation letter context uses full job.md |

## What NOT to change

- `raw/source_text.md` — still produced as the raw (possibly non-English) extraction
- `raw/extracted.json` — still produced for structured metadata
- The HTML download or markdown conversion — those work fine
- Translation scripts — they already work, just need to operate on full text

## Testing

1. Re-scrape job 201084, verify `job.md` contains the full posting (not just checklists)
2. Translate `job.md` and verify complete English text
3. Run `cv-tailor` and verify the LLM receives the full job description
4. Read `job.md` and confirm it's useful for deciding whether to apply
