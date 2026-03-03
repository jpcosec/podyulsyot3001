# Pipeline CLI — Redesigned Command Surface

This document describes the new unified CLI for the PhD application pipeline, introduced in Phase 9 of the pipeline redesign.

## Overview

The CLI uses a thin argparse dispatcher. `pipeline job <id> run` routes through `src/graph/pipeline.py` (graph-style coordinator with review interrupt/resume), while individual verbs remain available via `src/steps/*.py`.

The new command structure reduces ~27 old commands to 20 clear, hierarchical commands:

```
pipeline job <id> <verb>          # Single-job operations
pipeline jobs [--filter]          # Job queries
pipeline {ingest-url|...}         # Top-level admin
```

## Command Surface

### Job Workflow (Single-job operations)

Execute pipeline steps for a specific job. Each step reads inputs and produces outputs as defined in `src/utils/state.py`.

```bash
pipeline job <job_id> ingest            # Scrape + parse job posting
pipeline job <job_id> match             # Generate requirement-evidence mapping
pipeline job <job_id> match-approve     # Optional manual review lock (run --resume handles this automatically)
pipeline job <job_id> motivate          # Generate motivation letter content
pipeline job <job_id> tailor-cv         # Tailor CV from profile + matching
pipeline job <job_id> draft-email       # Generate application email
pipeline job <job_id> render            # Render CV + motivation to PDF
pipeline job <job_id> package           # Merge PDFs into Final_Application.pdf
pipeline job <job_id> status            # Show step completion + pending steps
pipeline job <job_id> run               # Graph-coordinated run until completion or review interrupt
pipeline job <job_id> run --resume      # Resume after editing planning/match_proposal.md
pipeline job <job_id> graph-status      # Inspect checkpointed graph state
pipeline job <job_id> regenerate <step> # Re-run a single step (reads comments)
```

### ATS Validation (Special commands, not pipeline steps)

```bash
pipeline job <job_id> validate-ats [--ats-target pdf|docx] [--via docx|latex]
pipeline job <job_id> template-test [--target pdf|docx] [--require-perfect]
```

### Job Queries

Filter and list open jobs.

```bash
pipeline jobs                           # List all open jobs
pipeline jobs --expiring <days>         # Jobs with deadline within N days
pipeline jobs --expired                 # Jobs past deadline
pipeline jobs --keyword <word>          # Filter by matching keyword
pipeline jobs --category <cat>          # Filter by job category
pipeline jobs --filter-by-property <k=v> # Filter by metadata property
pipeline jobs --filter-by-property tags=continue  # Filter by frontmatter tag
pipeline jobs --filter-by-property tags=review    # Filter review-marked jobs
```

### Ingestion Helpers

Fetch jobs directly (bypass normal listing crawl).

```bash
pipeline ingest-url <url> [<url>...]    # Fetch specific job URLs
pipeline ingest-listing <url>           # Crawl listing page
```

Both support:
- `--source <name>` (default: `tu_berlin`)

### Archive Management

Move jobs out of active pipeline.

```bash
pipeline archive <job_id>              # Archive specific job
pipeline archive --expired             # Archive all expired jobs
pipeline archive --marked              # Archive jobs marked in frontmatter
```

Archive markers read from `job.md` frontmatter include:
- `archive: true` / `archived: true`
- `status: archived`
- `tags: [archive]` (also accepts `reject`, `rejected`, `drop`)

### Marker-Driven Execution

Run next or all steps for jobs tagged in frontmatter (Obsidian-friendly triage).

```bash
pipeline run-marked                               # default tags continue,yes; run next step only
pipeline run-marked --tags continue,yes --mode all
pipeline run-marked --tags review,comments --mode next
```

### Admin Commands

```bash
pipeline index                         # Rebuild summary.csv and summary_detailed.csv
pipeline backup                        # Rebuild backup manifest
```

## Options

### Global Options (all job commands)

- `--force`: Re-run step even if outputs already exist
- `--resume`: Resume interrupted graph run (for `job <id> run`)
- `--source <name>`: Job source (default: `tu_berlin`)

### Rendering Options (render, validate-ats, template-test steps)

- `--via {docx|latex}`: Rendering engine (default: `docx`)
- `--docx-template {classic|modern|harvard|executive}`: DOCX template style (default: `modern`)
- `--language {english|german|spanish}`: Output language (default: `english`)

### Validation Options (validate-ats step)

- `--ats-target {pdf|docx}`: Format to validate (default: `pdf`)

### Template Test Options (template-test step)

- `--target {pdf|docx}`: Comparison target (default: `pdf`)
- `--require-perfect`: Fail if score < 100%

## Examples

```bash
# Single-job workflow
pipeline job 201084 ingest
pipeline job 201084 match
pipeline job 201084 render --via docx --docx-template modern
pipeline job 201084 package

# Graph run with review interrupt/resume
pipeline job 201084 run
pipeline job 201084 run --resume

# Re-run a step after making edits
pipeline job 201084 regenerate tailor-cv

# Validate rendering quality
pipeline job 201084 template-test --require-perfect
pipeline job 201084 validate-ats --ats-target pdf

# Query jobs
pipeline jobs
pipeline jobs --expiring 7
pipeline jobs --keyword bioprocess
pipeline jobs --expired

# Archive
pipeline archive 201084
pipeline archive --expired
```

## Architecture

### Graph Coordinator

`pipeline job <id> run` executes via `src/graph/pipeline.py`:

- Runs nodes in order: ingest -> match -> review_gate -> motivate -> tailor-cv -> draft-email -> render -> package
- Pauses at review_gate when `planning/reviewed_mapping.json` is missing
- Resumes with `pipeline job <id> run --resume` (auto-runs review lock)

### Step Registry

The CLI dispatch uses a static registry in `src/steps/__init__.py`:

```python
STEPS: dict[str, tuple[str, str]] = {
    "ingest":        ("src.steps.ingestion", "run"),
    "match":         ("src.steps.matching", "run"),
    "match-approve": ("src.steps.matching", "approve"),
    # ... etc
}
```

Each registry entry maps a verb to (module_path, function_name).

### Step Functions

All step functions follow the same signature:

```python
def run(state: JobState, *, force: bool = False, **kwargs) -> StepResult:
    """Execute the step.

    Args:
        state: JobState instance for target job
        force: Re-run even if complete
        **kwargs: Step-specific options

    Returns:
        StepResult(status="ok"|"skipped"|"error", produced=[...], comments_found=int, message=str)
    """
```

### JobState

Central source of truth for job paths and metadata:

```python
state = JobState(job_id="201084", source="tu_berlin")
state.job_dir                       # Root directory for job
state.metadata                      # Dict from raw/extracted.json
state.deadline                      # Parsed deadline date
state.step_complete("matching")    # Check if step done
state.pending_steps()              # List incomplete steps
state.read_artifact("cv/to_render.md")
state.write_artifact("cv/to_render.md", content)
```

See `src/utils/state.py` for full API.

### Comments System

Steps support inline feedback via HTML comments:

```markdown
## WORK EXPERIENCE

### 2022-01 -- Research Assistant -- TU Berlin -- Berlin
<!-- make this more specific to fermentation experience -->
- Conducted research on bioprocess optimization
```

Comments are extracted and logged to `.metadata/comments.jsonl` inside each job folder.

For matching, iterative review/regeneration also archives proposal rounds (`match_proposal.roundN.md`) and re-locks reviewed mappings on each round.

See `src/utils/comments.py` for utilities.

## Migration from Old CLI

Old commands → New commands:

| Old | New |
|---|---|
| `fetch-url <url>` | `ingest-url <url>` |
| `fetch-listing <url>` | `ingest-listing <url>` |
| `cv-tailor 201084` | `job 201084 tailor-cv` |
| `cv-build 201084` | `job 201084 render` |
| `cv-validate-ats 201084` | `job 201084 validate-ats` |
| `cv-template-test 201084` | `job 201084 template-test` |
| `status` | `job 201084 status` |
| `archive-passed --apply` | `archive --expired` |
| (no equivalent) | `job 201084 run` |
| (no equivalent) | `job 201084 regenerate <step>` |

## Testing

Run all CLI tests:

```bash
pytest tests/cli/test_pipeline.py -xvs
```

Test a specific command:

```bash
# Parse test only
pytest tests/cli/test_pipeline.py::test_parse_job_render_custom_options -xvs
```

## See Also

- `docs/plans/2026-03-02-pipeline-redesign-design.md` — Full design document
- `docs/pipeline/langgraph_run_hitl_testing_guide.md` — Graph run/resume + HITL + testing guide
- `docs/pipeline/match_review_regeneration_loop.md` — Match proposal iterative review loop
- `src/steps/` — Step implementations
- `src/utils/state.py` — JobState API
- `src/utils/comments.py` — Comment system
