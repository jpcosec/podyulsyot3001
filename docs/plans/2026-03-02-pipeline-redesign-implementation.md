# Pipeline Redesign — Implementation Plan

Date: 2026-03-02
Design doc: `docs/plans/2026-03-02-pipeline-redesign-design.md`
Current state analysis: `docs/pipeline/current_architecture_analysis.md`

## Overview

This plan breaks the redesign into 10 phases. Each phase is independently shippable, ends with a commit, and updates `changelog.md`. The old and new code coexist during migration — nothing breaks between phases.

Phases 1–6 build the new foundation. Phases 7–9 migrate logic. Phase 10 cleans up.

**Execution note:** Each phase is designed for a lower-capacity subagent. Context for each phase is self-contained — an agent only needs to read the files listed in "Context to read" plus this plan.

---

## Phase 1: Create `src/utils/state.py` — JobState class

### Context to read
- `docs/plans/2026-03-02-pipeline-redesign-design.md` (Section 6: JobState Class)
- `src/cv_generator/config.py` (current CVConfig — path resolution patterns)
- `src/cli/pipeline.py` lines 1–50 (REPO_ROOT, PIPELINE_ROOT constants) and functions: `get_pipeline_root_for_source`, `get_job_dir`, `get_app_dirs`, `ensure_app_dirs`, `_list_numeric_job_dirs`, `parse_deadline_date`, `read_job_deadline`

### Objective
Create `src/utils/state.py` with a `JobState` class that is the single source of truth for:
- Path resolution for any job artifact (replaces scattered path helpers)
- Job metadata access (reads `raw/extracted.json`)
- Step completion tracking (checks existence of step output files)
- Job lifecycle (open/archived status, archive operation)
- Class-level queries (list open jobs, filter by deadline, filter by keyword)

### What to build

```python
# src/utils/state.py

from dataclasses import dataclass
from pathlib import Path
from datetime import date, datetime
from functools import cached_property
import json

PIPELINE_ROOT = Path(__file__).resolve().parents[2] / "data" / "pipelined_data"
REFERENCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "reference_data"

class JobState:
    """Single source of truth for a job's paths, metadata, and artifact status."""

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

    def __init__(self, job_id: str, source: str = "tu_berlin"):
        self.job_id = job_id
        self.source = source
        self._source_root = PIPELINE_ROOT / source
        self._job_dir = self._source_root / job_id
        if self.is_archived:
            raise ValueError(f"Job {job_id} is archived and cannot be operated on")

    # Path resolution
    @property
    def job_dir(self) -> Path: ...
    def artifact_path(self, relative: str) -> Path: ...

    # Metadata from extracted.json
    @cached_property
    def metadata(self) -> dict: ...
    @property
    def deadline(self) -> date | None: ...
    @property
    def status(self) -> str: ...
    @property
    def is_archived(self) -> bool: ...

    # Step tracking
    def step_complete(self, step: str) -> bool: ...
    def pending_steps(self) -> list[str]: ...
    def completed_steps(self) -> list[str]: ...
    def next_step(self) -> str | None: ...

    # Artifact I/O
    def read_artifact(self, relative: str) -> str: ...
    def write_artifact(self, relative: str, content: str) -> Path: ...
    def read_json_artifact(self, relative: str) -> dict: ...
    def write_json_artifact(self, relative: str, data: dict) -> Path: ...

    # Lifecycle
    def archive(self) -> Path: ...  # moves job_dir to archive/job_id

    # Class-level queries
    @classmethod
    def list_open_jobs(cls, source: str = "tu_berlin") -> list["JobState"]: ...
    @classmethod
    def list_expiring(cls, days: int, source: str = "tu_berlin") -> list["JobState"]: ...
    @classmethod
    def list_expired(cls, source: str = "tu_berlin") -> list["JobState"]: ...
    @classmethod
    def list_by_keyword(cls, keyword: str, source: str = "tu_berlin") -> list["JobState"]: ...
```

### What to test
Create `tests/utils/test_state.py`:
- `test_job_dir_path_resolution` — verify paths are correct for a given job_id/source
- `test_artifact_path` — verify artifact_path returns correct absolute path
- `test_step_complete` — create fake step outputs, verify step_complete returns True/False
- `test_pending_steps` — verify pending_steps returns only incomplete steps
- `test_metadata_from_extracted_json` — create fake extracted.json, verify metadata access
- `test_deadline_parsing` — verify deadline property parses date correctly
- `test_is_archived` — verify archived detection (job dir under archive/)
- `test_archive_refuses_operation` — verify constructor raises for archived jobs
- `test_list_open_jobs` — create fake job dirs, verify listing excludes archive
- `test_list_expiring` — create jobs with deadlines, verify filtering

### Done criteria
- [ ] `src/utils/state.py` exists with full `JobState` class
- [ ] `tests/utils/test_state.py` passes (all tests above)
- [ ] `pytest tests/utils/test_state.py` exits 0
- [ ] No imports from `src/cli/pipeline.py` or `src/cv_generator/config.py` — JobState is independent
- [ ] Commit: `feat: add JobState class for unified path resolution and job lifecycle`
- [ ] Update `changelog.md`

---

## Phase 2: Create `src/utils/comments.py` — Comment system

### Context to read
- `docs/plans/2026-03-02-pipeline-redesign-design.md` (Section 4: Comment System)
- `src/cli/pipeline.py` functions: `collect_prep_comments`, `write_review_comments`, `COMMENT_PATTERN`

### Objective
Create `src/utils/comments.py` with comment extraction, collection, and logging. This is the backbone of the iterative feedback system.

### What to build

```python
# src/utils/comments.py

from dataclasses import dataclass, asdict
from pathlib import Path
import re, json
from datetime import datetime, timezone

COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)

@dataclass
class InlineComment:
    file: str       # relative path within job dir
    line: int       # 1-based line number
    text: str       # comment content (stripped of <!-- -->)
    context: str    # the line containing or surrounding the comment

def extract_comments(file_path: Path, job_dir: Path | None = None) -> list[InlineComment]:
    """Extract all <!-- ... --> comments from a file."""
    ...

def extract_comments_from_files(paths: list[Path], job_dir: Path) -> list[InlineComment]:
    """Extract comments from multiple files."""
    ...

@dataclass
class CommentLogEntry:
    step: str
    run_at: str  # ISO 8601
    comments: list[dict]

def load_comment_log(log_path: Path) -> list[CommentLogEntry]: ...

def append_to_comment_log(
    log_path: Path,
    step: str,
    comments: list[InlineComment],
) -> None:
    """Append a new entry to the comment log JSON file."""
    ...

def format_comments_for_prompt(comments: list[InlineComment]) -> str:
    """Format comments as a text block suitable for LLM prompt injection."""
    ...
```

### What to test
Create `tests/utils/test_comments.py`:
- `test_extract_single_comment` — one `<!-- text -->` in a file
- `test_extract_multiline_comment` — comment spanning multiple lines
- `test_extract_multiple_comments` — several comments, correct line numbers
- `test_extract_no_comments` — file with no comments returns empty list
- `test_context_captured` — verify surrounding line is captured
- `test_comment_log_append` — append entries, verify JSON structure
- `test_comment_log_accumulates` — multiple appends don't overwrite
- `test_format_for_prompt` — verify human-readable format output

### Done criteria
- [ ] `src/utils/comments.py` exists with all functions above
- [ ] `tests/utils/test_comments.py` passes
- [ ] `pytest tests/utils/test_comments.py` exits 0
- [ ] Commit: `feat: add comment extraction and logging system`
- [ ] Update `changelog.md`

---

## Phase 3: Create `src/steps/__init__.py` and step runner protocol

### Context to read
- `docs/plans/2026-03-02-pipeline-redesign-design.md` (Section 7: Step Function Signature)
- `src/utils/state.py` (from Phase 1)
- `src/utils/comments.py` (from Phase 2)

### Objective
Create the `src/steps/` package with the step runner protocol and a base helper that all steps will use.

### What to build

```python
# src/steps/__init__.py

from dataclasses import dataclass

@dataclass
class StepResult:
    status: str           # "ok", "skipped", "error"
    produced: list[str]   # relative paths of files written
    comments_found: int   # number of inline comments consumed
    message: str          # human-readable summary

# Step registry — maps CLI verb to (module, function)
STEPS: dict[str, tuple[str, str]] = {
    "ingest":      ("src.steps.ingestion", "run"),
    "match":       ("src.steps.matching", "run"),
    "match-approve": ("src.steps.matching", "approve"),
    "motivate":    ("src.steps.motivation", "run"),
    "tailor-cv":   ("src.steps.cv_tailoring", "run"),
    "draft-email": ("src.steps.email_draft", "run"),
    "render":      ("src.steps.rendering", "run"),
    "package":     ("src.steps.packaging", "run"),
}
```

```python
# src/steps/base.py

from src.utils.state import JobState
from src.utils.comments import (
    extract_comments, extract_comments_from_files,
    append_to_comment_log, format_comments_for_prompt,
)
from src.steps import StepResult

def gather_step_comments(
    state: JobState,
    step_name: str,
    own_outputs: list[str],
    input_files: list[str],
) -> tuple[list, str]:
    """
    Gather comments from step's own outputs and input files.
    Appends to comment log. Returns (comments_list, formatted_prompt_text).
    """
    all_comments = []
    for rel in own_outputs + input_files:
        path = state.artifact_path(rel)
        if path.exists():
            all_comments.extend(extract_comments(path, state.job_dir))

    if all_comments:
        log_path = state.artifact_path("planning/comments_log.json")
        append_to_comment_log(log_path, step_name, all_comments)

    prompt_text = format_comments_for_prompt(all_comments) if all_comments else ""
    return all_comments, prompt_text
```

### What to test
Create `tests/steps/test_base.py`:
- `test_gather_step_comments_from_own_output` — comments in step output file are found
- `test_gather_step_comments_from_inputs` — comments in input files are found
- `test_gather_appends_to_log` — verify comment log is written
- `test_gather_no_comments` — no comments returns empty list and empty prompt

### Done criteria
- [ ] `src/steps/__init__.py` exists with `StepResult` and `STEPS` registry
- [ ] `src/steps/base.py` exists with `gather_step_comments`
- [ ] `tests/steps/__init__.py` and `tests/steps/test_base.py` pass
- [ ] `pytest tests/steps/` exits 0
- [ ] Commit: `feat: add steps package with step protocol and comment-aware base`
- [ ] Update `changelog.md`

---

## Phase 4: Migrate ingestion step

### Context to read
- `src/scraper/scrape_single_url.py` — full file (the `run_for_url` function is the core)
- `src/scraper/fetch_listing.py` — full file (`crawl_listing` function)
- `src/scraper/generate_populated_tracker.py` — full file (`regenerate_job_markdown` function)
- `src/cli/pipeline.py` functions: `run_fetch_url`, `run_fetch_listing`, `run_fetch`, `run_regenerate`
- `src/utils/state.py` (from Phase 1)
- `src/steps/base.py` (from Phase 3)
- `docs/plans/2026-03-02-incremental-pipeline-fix/01-fix-scraping.md`

### Objective
Create `src/steps/ingestion.py` that wraps the existing scraper logic into the step protocol. The scraper modules (`src/scraper/*`) stay as implementation — the step is a thin orchestration layer.

### What to build

```python
# src/steps/ingestion.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False, url: str | None = None,
        strict_english: bool = True) -> StepResult:
    """
    Ingest a job posting. If url is provided, scrapes it.
    If not, checks if raw/raw.html exists and regenerates from it.
    """
    ...

def run_from_url(url: str, source: str = "tu_berlin", *,
                 strict_english: bool = True) -> StepResult:
    """Ingest from a URL. Creates JobState after extracting job_id."""
    ...

def run_from_listing(listing_url: str, source: str = "tu_berlin", *,
                     strict_english: bool = True, delay: float = 0.5) -> list[StepResult]:
    """Crawl a listing page and ingest all new jobs."""
    ...
```

**Key:** This step imports from `src/scraper/scrape_single_url` and `src/scraper/fetch_listing`. It does NOT duplicate their logic — it wraps them into the step protocol and uses `JobState` for paths.

### What to test
Create `tests/steps/test_ingestion.py`:
- `test_run_creates_expected_artifacts` — mock the scraper, verify step outputs match STEP_OUTPUTS
- `test_run_skips_when_complete` — verify step returns "skipped" when outputs exist and force=False
- `test_run_force_reruns` — verify force=True re-runs even when outputs exist
- `test_run_from_url_creates_job_state` — verify JobState is constructed from extracted job_id

### Done criteria
- [ ] `src/steps/ingestion.py` exists with `run`, `run_from_url`, `run_from_listing`
- [ ] Scraper modules (`src/scraper/*`) are NOT modified — ingestion.py wraps them
- [ ] `tests/steps/test_ingestion.py` passes
- [ ] `pytest tests/steps/test_ingestion.py` exits 0
- [ ] Commit: `feat: add ingestion step wrapping existing scrapers`
- [ ] Update `changelog.md`

---

## Phase 5: Migrate matching step

### Context to read
- `src/cv_generator/pipeline.py` — `MatchProposalPipeline` class and `parse_reviewed_proposal` function
- `src/models/pipeline_contract.py` — `ReviewedClaim`, `ReviewedMapping`, `EvidenceItem`
- `src/cli/pipeline.py` functions: `run_match_propose`, `run_match_approve`, `build_cv_tailoring`
- `src/utils/state.py` (from Phase 1)
- `src/steps/base.py` (from Phase 3)
- `docs/plans/2026-03-02-incremental-pipeline-fix/02-fix-matching.md`

### Objective
Create `src/steps/matching.py` that wraps `MatchProposalPipeline` into the step protocol. Add keyword extraction to the step output.

### What to build

```python
# src/steps/matching.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False) -> StepResult:
    """
    Generate match proposal from job + profile.
    Reads comments from own previous output and input files.
    Produces: planning/match_proposal.md, planning/keywords.json
    """
    ...

def approve(state: JobState) -> StepResult:
    """
    Parse reviewed match_proposal.md and lock reviewed_mapping.json.
    Produces: planning/reviewed_mapping.json
    """
    ...

def _extract_keywords(match_proposal_md: str, reviewed_mapping: dict) -> dict:
    """
    Extract keywords and categories from matching output.
    Returns {"keywords": [...], "categories": [...], "match_strength": float}
    """
    ...
```

### What to test
Create `tests/steps/test_matching.py`:
- `test_run_produces_proposal_and_keywords` — mock LLM, verify both outputs written
- `test_run_reads_comments_from_previous_output` — add comments to existing match_proposal.md, verify they're passed to prompt
- `test_approve_produces_reviewed_mapping` — create a reviewed proposal, verify JSON output
- `test_keywords_extraction` — verify keywords.json structure from sample proposal

### Done criteria
- [ ] `src/steps/matching.py` exists with `run`, `approve`, `_extract_keywords`
- [ ] Keywords.json is produced alongside match_proposal.md
- [ ] Comment reading from own output and job.md is wired
- [ ] `tests/steps/test_matching.py` passes
- [ ] `pytest tests/steps/test_matching.py` exits 0
- [ ] Commit: `feat: add matching step with keyword extraction and comment support`
- [ ] Update `changelog.md`

---

## Phase 6: Migrate motivation and email-draft steps

### Context to read
- `src/motivation_letter/service.py` — `MotivationLetterService` class (full file)
- `src/models/motivation.py` — `MotivationLetterOutput`, `EmailDraftOutput`
- `src/cli/pipeline.py` function: `run_motivation_build`
- `src/utils/state.py` (from Phase 1)
- `src/steps/base.py` (from Phase 3)
- `docs/plans/2026-03-02-incremental-pipeline-fix/03-fix-motivation.md`

### Objective
Split `MotivationLetterService` into two steps:
- `src/steps/motivation.py` — letter content generation (produces .md and .json)
- `src/steps/email_draft.py` — email draft from motivation summary + boilerplate (produces .md)

### What to build

```python
# src/steps/motivation.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False) -> StepResult:
    """
    Generate motivation letter content.
    Reads: job.md, reviewed_mapping.json, profile, prompts, comments
    Produces: planning/motivation_letter.md, planning/motivation_letter.json
    """
    ...
```

```python
# src/steps/email_draft.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False) -> StepResult:
    """
    Generate application email draft.
    Reads: planning/motivation_letter.json, job.md, comments
    Produces: planning/application_email.md
    """
    ...
```

**Key:** `MotivationLetterService` stays as implementation. The steps call its methods. Email draft logic is extracted from `generate_email_draft()` into the email_draft step.

### What to test
Create `tests/steps/test_motivation.py`:
- `test_run_produces_letter_artifacts` — mock LLM, verify .md and .json written
- `test_run_requires_reviewed_mapping` — verify error when mapping missing
- `test_run_reads_comments` — comments from own output and reviewed_mapping fed to prompt

Create `tests/steps/test_email_draft.py`:
- `test_run_produces_email` — mock motivation.json, verify email.md written
- `test_run_requires_motivation_output` — error when motivation_letter.json missing
- `test_email_contains_summary` — verify email references motivation content

### Done criteria
- [ ] `src/steps/motivation.py` exists with `run`
- [ ] `src/steps/email_draft.py` exists with `run`
- [ ] `MotivationLetterService` is NOT modified — steps wrap it
- [ ] `tests/steps/test_motivation.py` passes
- [ ] `tests/steps/test_email_draft.py` passes
- [ ] `pytest tests/steps/` exits 0
- [ ] Commit: `feat: add motivation and email-draft steps`
- [ ] Update `changelog.md`

---

## Phase 7: Migrate CV tailoring step

### Context to read
- `src/cv_generator/pipeline.py` — `CVTailoringPipeline` class
- `src/cv_generator/__main__.py` — `render_cv`, `build_cv`, `build_to_render_markdown`, `write_to_render_markdown`
- `src/cv_generator/config.py` — `CVConfig`
- `src/utils/state.py` (from Phase 1)
- `src/steps/base.py` (from Phase 3)

### Objective
Create `src/steps/cv_tailoring.py` that produces the CV content artifacts (.md only — no rendering).

### What to build

```python
# src/steps/cv_tailoring.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False, language: str = "english") -> StepResult:
    """
    Tailor CV content for this job.
    Reads: job.md, reviewed_mapping.json, profile, comments
    Produces: planning/cv_tailoring.md, cv/to_render.md
    """
    ...
```

**Key:** This step produces `cv/to_render.md` (the canonical render source) and `planning/cv_tailoring.md` (the tailoring brief). It does NOT render DOCX/PDF — that's the rendering step.

### What to test
Create `tests/steps/test_cv_tailoring.py`:
- `test_run_produces_tailoring_and_to_render` — mock LLM, verify both files
- `test_run_reads_comments` — comments from own output and mapping fed to prompt
- `test_to_render_md_structure` — verify output follows expected markdown structure

### Done criteria
- [ ] `src/steps/cv_tailoring.py` exists with `run`
- [ ] Step produces ONLY .md files (no DOCX/PDF/LaTeX)
- [ ] `tests/steps/test_cv_tailoring.py` passes
- [ ] `pytest tests/steps/test_cv_tailoring.py` exits 0
- [ ] Commit: `feat: add CV tailoring step (content only, no rendering)`
- [ ] Update `changelog.md`

---

## Phase 8: Migrate rendering step

### Context to read
- `src/render/docx.py` — `DocumentRenderer`
- `src/render/latex.py` — LaTeX rendering functions
- `src/render/pdf.py` — PDF text extraction
- `src/cv_generator/__main__.py` — `render_docx`, `render_latex`, `build_latex_pdf`, `convert_docx_to_pdf`
- `src/motivation_letter/service.py` — `build_pdf_for_job` method
- `src/cv_generator/ats.py` — ATS dual engine
- `src/utils/state.py` (from Phase 1)

### Objective
Create `src/steps/rendering.py` — the late-stage step that converts all validated `.md`/`.json` content into PDFs. This is the single place where DOCX/LaTeX/PDF generation happens.

### What to build

```python
# src/steps/rendering.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False,
        via: str = "docx",
        docx_template: str = "modern",
        docx_template_path: str | None = None,
        language: str = "english",
        targets: list[str] | None = None) -> StepResult:
    """
    Render all validated content to PDF.
    targets: ["cv", "motivation"] or None for all.

    Reads: cv/to_render.md, planning/motivation_letter.md
    Produces: output/cv.pdf, output/motivation_letter.pdf
    """
    ...

def render_cv(state: JobState, *, via: str = "docx",
              docx_template: str = "modern",
              docx_template_path: str | None = None,
              language: str = "english") -> Path:
    """Render CV to PDF. Returns path to output PDF."""
    ...

def render_motivation(state: JobState) -> Path:
    """Render motivation letter to PDF. Returns path to output PDF."""
    ...

def validate_ats(state: JobState, *, ats_target: str = "pdf",
                 via: str = "docx", file_stem: str = "cv") -> dict:
    """Run ATS validation on rendered CV. Returns ATS report dict."""
    ...

def template_test(state: JobState, *, via: str = "docx",
                  docx_template: str = "modern",
                  target: str = "pdf",
                  require_perfect: bool = False,
                  language: str = "english") -> dict:
    """Run deterministic parity check. Returns test results dict."""
    ...
```

### What to test
Create `tests/steps/test_rendering.py`:
- `test_run_renders_cv_pdf` — mock renderer, verify output/cv.pdf path produced
- `test_run_renders_motivation_pdf` — mock LaTeX, verify output/motivation_letter.pdf
- `test_run_skips_missing_sources` — if to_render.md missing, skip CV render gracefully
- `test_validate_ats_produces_report` — mock ATS engine, verify report dict

### Done criteria
- [ ] `src/steps/rendering.py` exists with `run`, `render_cv`, `render_motivation`, `validate_ats`, `template_test`
- [ ] Rendering uses `src/render/` engines (docx.py, latex.py) — no duplication
- [ ] ATS validation uses `src/cv_generator/ats.py` — no duplication
- [ ] `tests/steps/test_rendering.py` passes
- [ ] `pytest tests/steps/test_rendering.py` exits 0
- [ ] Commit: `feat: add rendering step — unified PDF generation for CV and motivation`
- [ ] Update `changelog.md`

---

## Phase 9: Migrate packaging step and rebuild CLI

### Context to read
- `src/utils/pdf_merger.py` — merge and compress functions
- `src/cli/pipeline.py` — `build_parser`, `main` (full functions)
- `src/steps/__init__.py` — STEPS registry (from Phase 3)
- `src/utils/state.py` (from Phase 1)
- All `src/steps/*.py` (from Phases 4–8)
- `docs/plans/2026-03-02-pipeline-redesign-design.md` (Section 5: CLI Command Surface)

### Objective
1. Create `src/steps/packaging.py` — merge PDFs into final submission
2. Rewrite `src/cli/pipeline.py` as a thin CLI that dispatches to steps

### What to build

```python
# src/steps/packaging.py

from src.utils.state import JobState
from src.steps import StepResult

def run(state: JobState, *, force: bool = False,
        output_name: str = "Final_Application.pdf") -> StepResult:
    """
    Merge all output PDFs into final submission.
    Reads: output/cv.pdf, output/motivation_letter.pdf
    Produces: output/Final_Application.pdf
    """
    ...
```

```python
# src/cli/pipeline.py — REWRITTEN (thin dispatch)

# Target: ~200-300 lines total
# Structure:
#   build_parser() — argparse with subcommands
#   main() — dispatch to step functions
#   No business logic in this file

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline", description="PhD application pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    # ── Job workflow ──
    job_parser = sub.add_parser("job", help="Single-job operations")
    job_parser.add_argument("job_id", help="Job ID")
    job_sub = job_parser.add_subparsers(dest="action", required=True)

    # job <id> ingest
    # job <id> match
    # job <id> match-approve
    # job <id> motivate
    # job <id> tailor-cv
    # job <id> draft-email
    # job <id> render
    # job <id> package
    # job <id> status
    # job <id> run
    # job <id> regenerate <step>
    # job <id> validate-ats
    # job <id> template-test

    # ── Ingestion helpers ──
    # ingest-url <url> [<url>...]
    # ingest-listing <url>

    # ── Job queries ──
    # jobs [--expiring N] [--expired] [--keyword X] [--category X]

    # ── Admin ──
    # archive <job_id> | --expired
    # index
    # backup
    ...

def main() -> int:
    args = build_parser().parse_args()
    if args.command == "job":
        state = JobState(args.job_id, source=getattr(args, "source", "tu_berlin"))
        step_fn = resolve_step(args.action)
        result = step_fn(state, **extract_step_args(args))
        print(result.message)
        return 0 if result.status != "error" else 1
    ...
```

### What to test
Update `tests/cli/test_pipeline.py`:
- `test_job_subcommand_routing` — verify `pipeline job 201084 match` routes to matching.run
- `test_jobs_listing` — verify `pipeline jobs --expiring 7` outputs correct jobs
- `test_archive_command` — verify `pipeline archive 201084` moves job dir

Create `tests/steps/test_packaging.py`:
- `test_run_merges_pdfs` — mock pdf_merger, verify Final_Application.pdf produced
- `test_run_requires_rendered_pdfs` — error when output/cv.pdf missing

### Done criteria
- [ ] `src/steps/packaging.py` exists with `run`
- [ ] `src/cli/pipeline.py` is rewritten as thin dispatch (~200-300 lines)
- [ ] ALL old commands are either mapped to new steps or explicitly removed
- [ ] `pipeline job <id> status` shows step completion table
- [ ] `pipeline jobs` lists open jobs with metadata (deadline, reference, category)
- [ ] `pipeline jobs --expiring 7` filters by deadline
- [ ] `pipeline jobs --keyword <word>` filters by matching keywords
- [ ] `tests/cli/test_pipeline.py` passes
- [ ] `tests/steps/test_packaging.py` passes
- [ ] `pytest tests/` exits 0 (full suite)
- [ ] Commit: `feat: rewrite CLI as thin dispatch + add packaging step`
- [ ] Update `changelog.md`

---

## Phase 10: Delete legacy code and clean up documentation

### Context to read
- `docs/pipeline/current_architecture_analysis.md` (Section 7: Dead Code and Ghosts)
- All `docs/` files (to assess which are legacy)
- `src/cv_generator/` directory listing
- `src/agent/` directory listing

### Objective
Delete all legacy/dead code identified in the architecture analysis. Update all documentation to reflect the new architecture. Remove docs that describe superseded flows.

### Files to delete

```
# Legacy code
src/cv_generator/renderer.py          # old table-based renderer
src/cv_generator/styles.py            # duplicate of src/render/styles.py
src/cv_generator/compile              # legacy CLI wrapper
src/cv_generator/Code/                # legacy data dir in code tree
src/cv_generator/DHIK_filled/         # legacy data dir in code tree
src/cv_generator/Txt/                 # legacy data dir in code tree
src/cv_generator/src/                 # legacy data dir in code tree
src/cv_generator/.env                 # should not be in code tree
src/build_word_cv.py                  # legacy hardcoded DOCX builder
src/ats_tester/backend/               # orphaned web app scaffolding
src/ats_tester/frontend/              # orphaned web app scaffolding
src/ats_tester/.venv/                 # leftover virtualenv
src/ats_tester/venv/                  # leftover virtualenv
src/ats_tester/.vscode/               # leftover IDE config
src/ats_tester/.git/                  # nested git repo (dangerous)
src/scraper/fetch_jobs.sh             # legacy shell wrapper
```

### Files to assess for deletion vs update in docs/

Review each file under `docs/` and decide:

| File | Action | Reason |
|------|--------|--------|
| `docs/pipeline/end_to_end_pipeline_deep_dive.md` | **Rewrite** | Describes old 27-command CLI, replace with new step-based architecture |
| `docs/pipeline/motivation_letter_system_deep_dive.md` | **Rewrite** | Describes old MotivationLetterService two-stage flow (deleted) |
| `docs/pipeline/command_surface_and_mutation_audit.md` | **Delete** | Superseded by new CLI — audit was for the old surface |
| `docs/pipeline/current_architecture_analysis.md` | **Keep** | Historical reference for why redesign happened |
| `docs/agents/unified_app_pipeline_skill.md` | **Delete** | Describes old app-prepare/review/renderize flow |
| `docs/AGENT_ENTRYPOINT.md` | **Rewrite** | References old CLI commands and old file layout |
| `docs/plans/2026-03-02-incremental-pipeline-fix/` | **Keep** | Historical context, already implemented |
| `docs/plans/2026-03-02-pipeline-redesign-design.md` | **Keep** | Design doc for this work |
| `docs/plans/2026-03-02-pipeline-redesign-implementation.md` | **Keep** | This plan |
| `docs/applications/TODO.md` | **Review** | May reference old commands |
| `docs/applications/Documentation_Checklist.md` | **Review** | May reference old paths |
| `docs/cv/ats_checker_deep_dive.md` | **Keep** | ATS unchanged |
| `docs/cv/ats-guidelines.md` | **Keep** | ATS unchanged |
| `docs/data/backup_compendium.md` | **Keep** | Backup unchanged |

### Documentation to create/update

1. **Rewrite `docs/pipeline/end_to_end_pipeline_deep_dive.md`** — new step DAG, data flow, CLI commands
2. **Rewrite `docs/pipeline/motivation_letter_system_deep_dive.md`** — new step-based motivation flow
3. **Create `docs/pipeline/data_flow.md`** — the data flow table from the design doc (which file is written by which step, read by which step)
4. **Update `CLAUDE.md`** — new CLI commands, new architecture, new file layout
5. **Update `README.md`** — new project structure, new commands
6. **Update `docs/AGENT_ENTRYPOINT.md`** — new CLI commands, new playbooks

### Renaming
- Consider renaming `src/cv_generator/` to `src/cv/` or leaving it if only `config.py`, `model.py`, `ats.py`, and `loaders/` remain (these are still CV-specific). The `__main__.py` should be deleted or reduced to a thin redirect to the new CLI.

### What to test
- `pytest tests/` exits 0 — no test breakage from deletions
- `python src/cli/pipeline.py --help` shows new command surface
- `python src/cli/pipeline.py job 201084 status` works
- No import errors from deleted modules

### Done criteria
- [ ] All files in "Files to delete" list are deleted
- [ ] All docs in "Action" column are handled (deleted/rewritten/kept)
- [ ] `docs/pipeline/data_flow.md` exists with the full step→file mapping
- [ ] `CLAUDE.md` updated with new commands and architecture
- [ ] `README.md` updated
- [ ] `pytest tests/` exits 0
- [ ] No import of deleted modules anywhere in codebase (grep to verify)
- [ ] Commit: `chore: delete legacy code and update documentation for pipeline redesign`
- [ ] Update `changelog.md`

---

## Execution Summary

| Phase | Description | Key deliverable | Estimated complexity |
|-------|-------------|-----------------|---------------------|
| 1 | JobState class | `src/utils/state.py` | Medium |
| 2 | Comment system | `src/utils/comments.py` | Low |
| 3 | Steps package + protocol | `src/steps/__init__.py`, `src/steps/base.py` | Low |
| 4 | Ingestion step | `src/steps/ingestion.py` | Medium |
| 5 | Matching step | `src/steps/matching.py` | Medium |
| 6 | Motivation + email steps | `src/steps/motivation.py`, `src/steps/email_draft.py` | Medium |
| 7 | CV tailoring step | `src/steps/cv_tailoring.py` | Medium |
| 8 | Rendering step | `src/steps/rendering.py` | High |
| 9 | Packaging + CLI rewrite | `src/steps/packaging.py`, `src/cli/pipeline.py` | High |
| 10 | Legacy cleanup + docs | Deletions + doc rewrites | Medium |

**Total: 10 commits, each independently shippable.**

## Dependencies

```
Phase 1 (JobState) ─────────────────┐
Phase 2 (Comments) ─────────────────┤
                                     ▼
Phase 3 (Steps protocol) ───────────┤
                                     ▼
Phase 4 (Ingestion) ────────────────┤
Phase 5 (Matching) ─────────────────┤  (4-8 can run in parallel
Phase 6 (Motivation + Email) ───────┤   after Phase 3 is done)
Phase 7 (CV Tailoring) ─────────────┤
Phase 8 (Rendering) ────────────────┤
                                     ▼
Phase 9 (Packaging + CLI) ──────────┤  (needs all steps)
                                     ▼
Phase 10 (Cleanup + Docs) ──────────┘  (needs everything)
```

Phases 4–8 have no dependencies on each other and can be parallelized.
