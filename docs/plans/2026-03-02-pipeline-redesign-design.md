# Pipeline Redesign — Architecture Design

Date: 2026-03-02

## Design Principles

1. **Data-first**: Every step produces `.json` or `.md`. No PDFs until rendering.
2. **Comment-driven iteration**: Users annotate any output with `<!-- comments -->`. Re-running a step reads comments from its own output AND its inputs, and incorporates them.
3. **Step = file contract**: Each step reads known input files, produces known output files. The pipeline is a DAG of file transformations.
4. **Archive isolation**: Archived jobs are invisible to the pipeline. No touching, no listing.
5. **Single orchestration path**: One CLI, one set of step functions. No parallel APIs.

## 1) Step DAG

```
                    ┌──────────┐
         URL/listing│ INGESTION│
                    └────┬─────┘
                         │ raw/raw.html, raw/source_text.md,
                         │ raw/extracted.json, job.md
                         ▼
                    ┌──────────┐
                    │ MATCHING │ ← profile_base_data.json
                    └────┬─────┘
                         │ planning/match_proposal.md
                         │ planning/reviewed_mapping.json
                         │ planning/keywords.json
                         ▼
              ┌──────────┴──────────┐
              ▼                     ▼
      ┌──────────────┐     ┌──────────────┐
      │  MOTIVATION  │     │ CV-TAILORING │  (parallel, both read matching)
      └──────┬───────┘     └──────┬───────┘
             │                    │
             │ planning/          │ planning/cv_tailoring.md
             │  motivation_       │ cv/to_render.md
             │  letter.md         │
             │  motivation_       │
             │  letter.json       │
             ▼                    │
      ┌──────────────┐           │
      │  EMAIL-DRAFT │           │
      └──────┬───────┘           │
             │ planning/          │
             │  application_      │
             │  email.md          │
             ▼                    ▼
         ┌───────────────────────────┐
         │        RENDERING          │  ← validates all content first
         └────────────┬──────────────┘
                      │ output/cv.pdf
                      │ output/motivation_letter.pdf
                      ▼
                ┌───────────┐
                │ PACKAGING │
                └─────┬─────┘
                      │ output/Final_Application.pdf
                      ▼
                    DONE
```

## 2) Source Tree

```
src/
  cli/
    pipeline.py              # Thin argparse + dispatch (~200 lines)
  steps/
    __init__.py
    ingestion.py             # Scrape, parse, create job dir + job.md
    matching.py              # Requirement-evidence mapping + keywords
    motivation.py            # Motivation letter content generation
    cv_tailoring.py          # CV tailoring from profile + matching
    email_draft.py           # Email summary from motivation + boilerplate
    rendering.py             # Validated .md/.json → PDF (CV + motivation)
    packaging.py             # Merge PDFs → final submission
  render/                    # Rendering engines (unchanged)
    docx.py, latex.py, pdf.py, styles.py, templates/, assets/
  models/                    # Data contracts (unchanged)
    job.py, application.py, motivation.py, pipeline_contract.py
  utils/
    gemini.py                # LLM transport (unchanged)
    loader.py                # Data loading helpers (unchanged)
    pdf_merger.py            # PDF merge + compression (unchanged)
    nlp/                     # Text analysis (unchanged)
    state.py                 # NEW: JobState — path resolution + artifact tracking
    comments.py              # NEW: Comment extraction + collection
  ats_tester/
    deterministic_evaluator.py  # Unchanged
  prompts/                   # Unchanged
```

### What gets deleted

- `src/cv_generator/renderer.py` — legacy table-based header
- `src/cv_generator/styles.py` — legacy duplicate of `src/render/styles.py`
- `src/cv_generator/compile` — legacy CLI wrapper
- `src/cv_generator/Code/`, `DHIK_filled/`, `Txt/`, `src/` — legacy data dirs in code tree
- `src/build_word_cv.py` — legacy hardcoded DOCX builder
- `src/ats_tester/backend/`, `frontend/`, `.git` — orphaned web app scaffolding
- `translate` command — dead no-op
- legacy motivation command reference — broken reference

### What gets absorbed/refactored

| Current location | New location | Notes |
|---|---|---|
| `src/cli/pipeline.py` (2149 lines) | `src/cli/pipeline.py` (~200 lines) + `src/steps/*` | Monolith split |
| `src/scraper/*` | `src/steps/ingestion.py` | Three scripts → one step |
| `src/cv_generator/pipeline.py` | `src/steps/cv_tailoring.py` + `src/steps/matching.py` | Split by domain |
| `src/cv_generator/__main__.py` | `src/steps/cv_tailoring.py` + `src/steps/rendering.py` | Split content from rendering |
| `src/cv_generator/config.py` | `src/utils/state.py` | CVConfig → JobState |
| `src/cv_generator/ats.py` | `src/ats_tester/` (stays, used by rendering step) | ATS stays separate |
| `src/motivation_letter/service.py` | `src/steps/motivation.py` + `src/steps/email_draft.py` | Split letter from email |
| `src/agent/` | Parked (not deleted) | Future work |
| Path helpers in pipeline.py | `src/utils/state.py` | Proper class |
| Comment workflow in pipeline.py | `src/utils/comments.py` | Reusable |

### What stays unchanged

- `src/render/` — clean, focused, works
- `src/models/` — good contracts
- `src/utils/gemini.py` — shared LLM transport
- `src/utils/pdf_merger.py` — works
- `src/prompts/` — prompt files
- `src/ats_tester/deterministic_evaluator.py` — works

## 3) Job Metadata and Lifecycle

### 3.1 Job metadata contract

`raw/extracted.json` is the structured source of truth for job metadata:

```json
{
  "status": "open",
  "deadline": "2026-03-06",
  "reference_number": "III-51/26",
  "university": "TU Berlin",
  "category": "Research Associate",
  "contact_person": "Prof. Dr.-Ing. Franz Dietrich",
  "contact_email": "sabine.lange@tu-berlin.de",
  "url": "https://www.jobs.tu-berlin.de/en/job-postings/201399",
  "title": "Research Assistant in Bioprocess Engineering",
  "language": "english",
  "ingested_at": "2026-03-02T14:30:00Z"
}
```

`job.md` carries the same data as YAML frontmatter (human-readable mirror):

```yaml
---
status: open
deadline: 2026-03-06
reference_number: III-51/26
university: TU Berlin
category: Research Associate
url: https://www.jobs.tu-berlin.de/en/job-postings/201399
---
```

The `JobState` class reads `extracted.json` for programmatic access. Frontmatter in `job.md` is for human convenience.

### 3.2 Job lifecycle states

```
open → archived
         ↑
    (deadline passed, or manual archive)
```

- **open**: visible to all pipeline operations and queries
- **archived**: moved to `data/pipelined_data/<source>/archive/<job_id>/`. Pipeline ignores it completely.

`JobState` constructor refuses to operate on archived jobs. Archive is a one-way move.

### 3.3 Deadline-based operations

```bash
pipeline jobs --expiring 7          # Jobs with deadline within 7 days
pipeline jobs --expired             # Jobs past deadline (candidates for archive)
pipeline archive --expired          # Move all expired jobs to archive
pipeline archive <job_id>           # Archive specific job
```

### 3.4 Keywords from matching

`matching` step produces `planning/keywords.json`:

```json
{
  "keywords": ["bioprocess", "fermentation", "downstream", "python", "matlab"],
  "categories": ["bioprocess-engineering", "data-analysis"],
  "match_strength": 0.73
}
```

This enables:

```bash
pipeline jobs --keyword bioprocess  # Filter jobs by matching keywords
pipeline jobs --category research   # Filter by category
```

## 4) Comment System

### 4.1 How comments work

Any `.md` output can contain inline HTML comments:

```markdown
## WORK EXPERIENCE

### 2022-01 -- Research Assistant -- TU Berlin -- Berlin
<!-- make this more specific to fermentation experience -->
- Conducted research on bioprocess optimization
- Published 3 papers on downstream processing
<!-- add the MATLAB simulation project -->
```

### 4.2 Comment extraction

`src/utils/comments.py` provides:

```python
@dataclass
class InlineComment:
    file: str           # relative path within job dir
    line: int           # line number
    text: str           # comment content (stripped of <!-- -->)
    context: str        # surrounding line(s) for reference

def extract_comments(file_path: Path) -> list[InlineComment]: ...
def extract_comments_from_dir(job_dir: Path) -> list[InlineComment]: ...
```

### 4.3 Comment flow per step

When a step runs, it:

1. **Reads comments from its own previous output** (if it exists) — these are direct revision instructions.
2. **Reads comments from its input files** — these are upstream context that may influence generation.
3. **Collects all comments into `planning/comments_log.json`** — persistent record for future reference.
4. **Passes comments as context** to the generation prompt (for LLM-driven steps) or applies them as rules (for deterministic steps).

```python
# Inside any step function:
def run(state: JobState, **kwargs):
    # 1. Gather comments from own output + inputs
    own_comments = extract_comments(state.artifact_path("planning/motivation_letter.md"))
    input_comments = extract_comments(state.artifact_path("planning/reviewed_mapping.json"))

    # 2. Log them
    state.append_comments("motivation", own_comments + input_comments)

    # 3. Use them in generation
    context = build_context(state, comments=own_comments + input_comments)
    result = generate(context)

    # 4. Write output (comments are consumed, not preserved in output)
    state.write_artifact("planning/motivation_letter.md", result)
```

### 4.4 Comment log

`planning/comments_log.json` accumulates across runs:

```json
{
  "entries": [
    {
      "step": "matching",
      "run_at": "2026-03-02T15:00:00Z",
      "comments": [
        {
          "file": "planning/match_proposal.md",
          "line": 42,
          "text": "this requirement is about wet lab, not dry lab",
          "context": "- Requirement: Laboratory experience"
        }
      ]
    }
  ]
}
```

This log is especially valuable for matching — accumulated comments become a knowledge base about how the user interprets requirements.

## 5) CLI Command Surface

```bash
# ── Job workflow (single-job, the main path) ──
pipeline job <job_id> ingest            # Scrape + parse
pipeline job <job_id> match             # Generate match proposal
pipeline job <job_id> match-approve     # Lock reviewed mapping
pipeline job <job_id> motivate          # Generate motivation letter
pipeline job <job_id> tailor-cv         # Tailor CV content
pipeline job <job_id> draft-email       # Generate email draft
pipeline job <job_id> render            # All validated → PDF
pipeline job <job_id> package           # Merge → final PDF
pipeline job <job_id> status            # Step completion + comments
pipeline job <job_id> run               # Execute all pending steps
pipeline job <job_id> regenerate <step> # Re-run one step (reads comments)

# ── Ingestion helpers ──
pipeline ingest-url <url> [<url>...]    # Fetch specific URLs
pipeline ingest-listing <url>           # Crawl listing page

# ── Job queries ──
pipeline jobs                           # List all open jobs
pipeline jobs --expiring <days>         # Filter by deadline proximity
pipeline jobs --expired                 # Past deadline
pipeline jobs --keyword <word>          # Filter by matching keywords
pipeline jobs --category <cat>          # Filter by category

# ── Admin ──
pipeline archive <job_id>              # Archive specific job
pipeline archive --expired             # Archive all expired
pipeline index                         # Rebuild job index
pipeline backup                        # Rebuild backup manifest

# ── ATS (validation, not a pipeline step) ──
pipeline job <job_id> validate-ats     # ATS score on rendered CV
pipeline job <job_id> template-test    # Deterministic parity check
```

**27 commands → 20**, but with much clearer structure:
- `pipeline job <id> <verb>` for single-job operations
- `pipeline jobs` for queries
- Top-level for admin/batch

## 6) JobState Class

```python
class JobState:
    """Single source of truth for a job's paths, metadata, and artifact status."""

    PIPELINE_ROOT = Path("data/pipelined_data")
    ARCHIVE_DIR = "archive"

    STEP_OUTPUTS: dict[str, list[str]] = {
        "ingestion":    ["raw/raw.html", "raw/source_text.md", "raw/extracted.json", "job.md"],
        "matching":     ["planning/match_proposal.md", "planning/reviewed_mapping.json",
                         "planning/keywords.json"],
        "motivation":   ["planning/motivation_letter.md", "planning/motivation_letter.json"],
        "cv_tailoring": ["planning/cv_tailoring.md", "cv/to_render.md"],
        "email_draft":  ["planning/application_email.md"],
        "rendering":    ["output/cv.pdf", "output/motivation_letter.pdf"],
        "packaging":    ["output/Final_Application.pdf"],
    }

    STEP_ORDER = [
        "ingestion", "matching", "motivation",
        "cv_tailoring", "email_draft", "rendering", "packaging",
    ]

    def __init__(self, job_id: str, source: str = "tu_berlin"): ...

    # ── Paths ──
    @property
    def job_dir(self) -> Path: ...
    def artifact_path(self, relative: str) -> Path: ...

    # ── Metadata (from extracted.json) ──
    @cached_property
    def metadata(self) -> dict: ...
    @property
    def deadline(self) -> date | None: ...
    @property
    def status(self) -> str: ...
    @property
    def is_archived(self) -> bool: ...

    # ── Step tracking ──
    def step_complete(self, step: str) -> bool: ...
    def pending_steps(self) -> list[str]: ...
    def has_comments(self, step: str) -> bool: ...

    # ── Artifact I/O ──
    def read_artifact(self, relative: str) -> str: ...
    def write_artifact(self, relative: str, content: str) -> Path: ...
    def read_json_artifact(self, relative: str) -> dict: ...
    def write_json_artifact(self, relative: str, data: dict) -> Path: ...

    # ── Comment log ──
    def append_comments(self, step: str, comments: list[InlineComment]) -> None: ...
    def comment_history(self, step: str | None = None) -> list[dict]: ...

    # ── Lifecycle ──
    def archive(self) -> None: ...

    # ── Class-level queries ──
    @classmethod
    def list_open_jobs(cls, source: str = "tu_berlin") -> list["JobState"]: ...
    @classmethod
    def list_expiring(cls, days: int, source: str = "tu_berlin") -> list["JobState"]: ...
    @classmethod
    def list_by_keyword(cls, keyword: str, source: str = "tu_berlin") -> list["JobState"]: ...
```

## 7) Step Function Signature

Every step follows the same pattern:

```python
def run(state: JobState, *, force: bool = False, **step_specific_args) -> dict:
    """
    Execute the step for a job.

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist

    Returns:
        dict with keys: {"produced": [...], "comments_found": int, "status": "ok"|"error"}
    """
```

This uniform interface means the CLI dispatch is trivial:

```python
STEPS = {
    "ingest": ingestion.run,
    "match": matching.run,
    "motivate": motivation.run,
    "tailor-cv": cv_tailoring.run,
    "draft-email": email_draft.run,
    "render": rendering.run,
    "package": packaging.run,
}
```

## 8) Data Flow Summary

```
File                              Written by        Read by
─────────────────────────────────────────────────────────────
raw/raw.html                      ingestion         (reference)
raw/source_text.md                ingestion         matching, motivation
raw/extracted.json                ingestion         JobState.metadata, matching
job.md                            ingestion         matching, motivation, cv_tailoring, email_draft
planning/match_proposal.md        matching          (human review)
planning/reviewed_mapping.json    matching          motivation, cv_tailoring
planning/keywords.json            matching          JobState queries
planning/motivation_letter.md     motivation        email_draft, rendering
planning/motivation_letter.json   motivation        email_draft
planning/cv_tailoring.md          cv_tailoring      (reference)
planning/application_email.md     email_draft       (reference)
cv/to_render.md                   cv_tailoring      rendering
planning/comments_log.json        all steps         all steps (accumulated)
output/cv.pdf                     rendering         packaging
output/motivation_letter.pdf      rendering         packaging
output/Final_Application.pdf      packaging         (submission)
```

## 9) Migration Strategy

The redesign can be done incrementally:

1. **Phase 1**: Create `src/utils/state.py` and `src/utils/comments.py`. No behavior change.
2. **Phase 2**: Create `src/steps/` with one step at a time, starting with `ingestion.py`. Wire it into existing CLI alongside old commands.
3. **Phase 3**: Migrate remaining steps one by one. Each step is independently testable.
4. **Phase 4**: Replace `src/cli/pipeline.py` with thin dispatch. Delete old commands.
5. **Phase 5**: Delete legacy files and empty packages.

Each phase is independently shippable. The old and new paths coexist during migration.
