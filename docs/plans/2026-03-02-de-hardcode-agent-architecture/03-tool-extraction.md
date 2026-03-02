# Step 03 — Tool Extraction

## Goal
Extract reusable tool functions from the existing codebase (scraper, renderer, ATS, motivation letter) into `src/agent/tools.py`. Each tool is a standalone callable with typed input/output that the agent orchestrator can invoke. These are the "hands" of the system — deterministic operations the LLM agent delegates to.

## Depends on
- **01-pydantic-models** — tools use the Pydantic models for typed I/O
- **02-prompts-to-src** — motivation tools use the prompt loader

## Files to Read First
- `src/scraper/scrape_single_url.py` — `run_for_url()`, `download_html()`, `extract_full_text_markdown()`, `parse_structured_from_markdown()`, `render_tracker_markdown()`
- `src/render/docx.py` — `DocumentRenderer` class
- `src/cv_generator/__main__.py` — `do_build()` flow (profile → model → render → pdf)
- `src/cv_generator/ats.py` — `run_ats_analysis()`, `run_code_engine()`, `run_llm_engine()`
- `src/motivation_letter/service.py` — `build_context()`, `generate_for_job()`, `build_pdf_for_job()`
- `src/cv_generator/model.py` — `CVModel.from_profile()`
- `src/cv_generator/loaders/profile_loader.py` — `load_base_profile()`
- `src/models/` — all models created in step 01

## Files to Create

### `src/agent/__init__.py`
Empty.

### `src/agent/tools.py`
A module of tool functions. Each function:
- Has a clear docstring (Gemini uses these for tool descriptions)
- Takes typed arguments, returns typed results
- Does one thing — no orchestration logic
- Handles its own errors (returns error info, doesn't crash)

```python
"""Tool functions for the application agent.

Each function is a standalone operation the agent can invoke.
Tools are deterministic (scrape, render, score) or LLM-driven
(analyze fit, tailor CV, write motivation letter).
"""

from pathlib import Path
from src.models.job import JobPosting
from src.models.application import FitAnalysis
from src.models.motivation import MotivationLetterOutput, EmailDraftOutput
from src.models.pipeline_contract import PipelineState
from src.cv_generator.config import CVConfig


# ── Ingestion Tools ──────────────────────────────────────────────

def scrape_job(url: str, config: CVConfig | None = None) -> JobPosting:
    """Scrape a job posting URL and return structured job data.

    Downloads HTML, extracts markdown, parses to structured fields,
    writes raw artifacts to pipeline data directory.
    """
    # Wraps: scrape_single_url.run_for_url() + parse_structured_from_markdown()
    # Returns: JobPosting.from_summary_json(summary)
    ...


def scrape_jobs_batch(urls: list[str], config: CVConfig | None = None) -> list[JobPosting]:
    """Scrape multiple job URLs in sequence. Returns list of parsed jobs."""
    ...


# ── Analysis Tools (LLM-driven) ─────────────────────────────────

def analyze_fit(job: JobPosting, profile_path: Path | None = None) -> FitAnalysis:
    """Analyze how well a candidate profile fits a job posting.

    Uses the ATS evaluation prompt with Gemini to score alignment.
    Returns structured fit analysis with score, matches, gaps.
    """
    # Loads profile, builds context, calls Gemini with ats_evaluation prompt
    # Parses response into FitAnalysis model
    ...


def rank_jobs(jobs: list[JobPosting], profile_path: Path | None = None) -> list[tuple[JobPosting, FitAnalysis]]:
    """Rank multiple jobs by fit score. Returns sorted (job, fit) pairs."""
    ...


# ── CV Tools ─────────────────────────────────────────────────────

def tailor_cv(
    job: JobPosting,
    pipeline_state: PipelineState,
    config: CVConfig | None = None,
) -> PipelineState:
    """Run the multi-agent CV tailoring pipeline (MATCHER → SELLER → CHECKER).

    Takes a job and initial pipeline state (with evidence), returns
    the final state with approved claims.
    """
    # Wraps: CVMultiAgentPipeline.execute_pipeline() (after step 04 fixes it)
    ...


def render_cv(
    job_id: str,
    source: str = "tu_berlin",
    template: str = "modern",
    via: str = "docx",
    config: CVConfig | None = None,
) -> Path:
    """Render a CV to DOCX or LaTeX and convert to PDF.

    Returns path to the generated PDF.
    """
    # Wraps: the build flow in __main__.py do_build()
    # profile → CVModel → DocumentRenderer → soffice → PDF
    ...


def score_ats(
    job_id: str,
    source: str = "tu_berlin",
    ats_target: str = "pdf",
    config: CVConfig | None = None,
) -> dict:
    """Run ATS validation on a rendered CV.

    Returns the ATS report dict with code_score, llm_score, combined, parity.
    """
    # Wraps: run_ats_analysis() from ats.py
    ...


# ── Motivation Tools (LLM-driven) ───────────────────────────────

def plan_motivation_letter(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> dict:
    """Create a motivation letter section plan using the pre-letter agent.

    Returns the section plan with evidence assignments and gaps.
    """
    # Uses: load_prompt_with_context("motivation_pre_letter", context_json)
    # Calls Gemini, validates against Pydantic schema
    ...


def write_motivation_letter(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> MotivationLetterOutput:
    """Generate the final motivation letter using the motivation agent.

    Returns structured letter output with subject, salutation, body.
    """
    # Uses: load_prompt_with_context("motivation_letter", context_json)
    # Calls Gemini, validates against MotivationLetterOutput schema
    ...


def build_motivation_pdf(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> Path:
    """Render a motivation letter markdown to PDF via LaTeX.

    Returns path to the generated PDF.
    """
    # Wraps: MotivationLetterService.build_pdf_for_job()
    ...


def generate_email_draft(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> EmailDraftOutput:
    """Generate an application email draft using the email agent.

    Returns structured email with subject, body, signature.
    """
    # Uses: load_prompt_with_context("email_draft", context_json)
    # Calls Gemini, validates against EmailDraftOutput schema
    ...


# ── Utility Tools ────────────────────────────────────────────────

def merge_pdfs(output_path: Path, *pdf_paths: Path) -> Path:
    """Merge multiple PDFs into one. Returns output path."""
    # Wraps: src/utils/pdf_merger.py logic
    ...
```

## Specification

### Design Principles

1. **Tools are functions, not classes.** The orchestrator calls them by name. No state between calls.
2. **Each tool wraps existing code.** Don't rewrite the scraper or renderer — import and call them. The tool function is a thin typed adapter.
3. **Config defaults to `CVConfig.from_defaults()`.** Tools work standalone without explicit config.
4. **LLM-driven tools follow the pattern:**
   ```python
   def some_tool(job_id, ...) -> SomeModel:
       context = build_context(...)
       prompt = load_prompt_with_context("prompt_name", json.dumps(context))
       response = gemini_client.generate(prompt)
       return SomeModel.model_validate_json(response)
   ```
5. **No orchestration logic in tools.** `tailor_cv` runs the pipeline but doesn't decide WHETHER to tailor. That's the orchestrator's job.

### What Each Tool Wraps

| Tool | Wraps | Deterministic? |
|---|---|---|
| `scrape_job` | `scrape_single_url.run_for_url()` + `parse_structured_from_markdown()` | Yes |
| `scrape_jobs_batch` | Loop of `scrape_job` | Yes |
| `analyze_fit` | Gemini call with `ats_evaluation` prompt | No (LLM) |
| `rank_jobs` | Loop of `analyze_fit` + sort | No (LLM) |
| `tailor_cv` | `CVMultiAgentPipeline.execute_pipeline()` | No (LLM) |
| `render_cv` | `__main__.py:do_build()` flow | Yes |
| `score_ats` | `ats.py:run_ats_analysis()` | Hybrid (code + LLM) |
| `plan_motivation_letter` | Gemini call with `motivation_pre_letter` prompt | No (LLM) |
| `write_motivation_letter` | Gemini call with `motivation_letter` prompt | No (LLM) |
| `build_motivation_pdf` | `service.py:build_pdf_for_job()` | Yes |
| `generate_email_draft` | Gemini call with `email_draft` prompt | No (LLM) |
| `merge_pdfs` | `pdf_merger.py` logic | Yes |

### GeminiClient Usage
All LLM-driven tools should use the existing `src/utils/gemini.py:GeminiClient`. Instantiate once at module level:

```python
from src.utils.gemini import GeminiClient
_gemini = None

def _get_gemini() -> GeminiClient:
    global _gemini
    if _gemini is None:
        _gemini = GeminiClient()
    return _gemini
```

## Verification
```bash
cd /home/jp/phd

# 1. Module imports without error
python -c "
from src.agent.tools import scrape_job, analyze_fit, tailor_cv, render_cv
from src.agent.tools import score_ats, plan_motivation_letter, write_motivation_letter
from src.agent.tools import build_motivation_pdf, generate_email_draft, merge_pdfs
print('All tool functions importable.')
"

# 2. Deterministic tool works (scrape - needs network, so test with existing data)
python -c "
from src.agent.tools import render_cv
from pathlib import Path
# Just verify the function signature accepts expected args
import inspect
sig = inspect.signature(render_cv)
params = list(sig.parameters.keys())
assert 'job_id' in params
assert 'template' in params
assert 'via' in params
print('Tool signatures correct.')
"

# 3. scrape_job returns a JobPosting
python -c "
from src.agent.tools import scrape_job
from src.models.job import JobPosting
import inspect
sig = inspect.signature(scrape_job)
assert sig.return_annotation == JobPosting or 'JobPosting' in str(sig.return_annotation)
print('scrape_job returns JobPosting.')
"
```

## Done Criteria
- [ ] `src/agent/__init__.py` exists
- [ ] `src/agent/tools.py` contains all 12 tool functions listed above
- [ ] Each tool function has a docstring, typed arguments, and typed return
- [ ] Deterministic tools wrap existing code (import + call, don't rewrite)
- [ ] LLM-driven tools use `src/prompts/` loader and `GeminiClient`
- [ ] Module imports without error
- [ ] Verification script exits 0
