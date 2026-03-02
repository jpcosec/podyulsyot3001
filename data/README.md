# Data Layout

The `data/` directory has two top-level categories:

- `pipelined_data/`: generated artifacts produced by the scraping/application pipeline.
- `reference_data/`: static or semi-static inputs used to generate/guide pipeline outputs.

## Pipeline Convention

For website-driven jobs, the canonical order is:

`data/pipelined_data/{website_source}/{job_id}/{document}`

Current website source:
- `tu_berlin`

Typical documents per job:
- `raw.html`
- `proposal_text.md`
- `summary.json`
- `job.md`
- `motivation_letter.md` (optional)

Typical CV subtree per job:

- `cv/rendered/cv.pdf` (final artifact)
- `cv/rendered/cv.docx` (when built via DOCX)
- `cv/rendered/cv.tex` (when built via LaTeX)
- `cv/ats/report.json` (ATS results)
- `cv/to_render.md` (auto-generated parity source for deterministic content checks)

## Pipeline CLI

Run the canonical pipeline from repository root:

```bash
python src/cli/pipeline.py run
```

Validate required files:

```bash
python src/cli/pipeline.py validate
```

Build CV PDF and run ATS validation:

```bash
python src/cli/pipeline.py cv-pdf <job_id> english --via docx --docx-template modern
```

Run deterministic template parity test (100% gate on DOCX target):

```bash
python src/cli/pipeline.py cv-template-test <job_id> english --via docx --target docx --require-perfect
```
