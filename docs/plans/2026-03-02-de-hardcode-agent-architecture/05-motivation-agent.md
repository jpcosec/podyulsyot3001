# Step 05 — Rebuild Motivation Letter as Agent-Driven

## Goal
Rebuild the motivation letter flow to be fully agent-driven. Delete the hardcoded scaffolding logic (`_build_section_plan()`, `_render_pre_letter()`, keyword/threshold matching, hardcoded email draft). Replace with two LLM agent calls: one for planning (pre-letter), one for generation. The `build_context()` method and PDF rendering stay — they're data assembly and deterministic rendering, not scaffolding.

## Depends on
- **01-pydantic-models** — uses `MotivationLetterOutput`, `EmailDraftOutput`
- **02-prompts-to-src** — uses `motivation_pre_letter.txt`, `motivation_letter.txt`, `email_draft.txt`

## Files to Read First
- `src/motivation_letter/service.py` — full class, understand all methods
- `src/prompts/motivation_pre_letter.txt` — the new planning prompt (created in step 02)
- `src/prompts/motivation_letter.txt` — existing generation prompt
- `src/prompts/email_draft.txt` — new email prompt (created in step 02)
- `src/models/motivation.py` — `MotivationLetterOutput`, `EmailDraftOutput` (created in step 01)
- `src/utils/gemini.py` — `GeminiClient`

## Files to Modify

### `src/motivation_letter/service.py` — MAJOR REWRITE

#### Methods to DELETE (hardcoded scaffolding):
- `_build_section_plan()` — hardcoded keyword sets ("python", "workflow", "mlops", "airflow", "model") selecting evidence by substring. Replaced by the pre-letter agent.
- `_render_pre_letter()` — hardcoded markdown template with fixed section headers. Replaced by agent output.
- `_select_evidence_ids_by_keywords()` — helper for the deleted `_build_section_plan()`.
- `_collect_coverage_evidence_ids()` — helper for the deleted `_build_section_plan()`.
- `_format_evidence_refs()` — helper for the deleted `_build_section_plan()`.
- `_summarize_requirement_for_email()` — helper for the deleted `generate_email_draft()`.
- `generate_email_draft()` body — the current implementation hardcodes paragraph text. Rebuild to use LLM.

#### Methods to KEEP (data assembly + rendering):
- `__init__()` — config, paths setup (update to use prompt loader)
- `build_context()` — reads job.md, loads profile, builds evidence catalog. This is pure data assembly, not scaffolding. Keep it.
- `_build_evidence_catalog()` — creates atomic evidence items from profile. Keep.
- `_parse_frontmatter()` — YAML parsing. Keep.
- `_extract_checklist_items()` — markdown parsing. Keep.
- `_extract_bullet_items()` — markdown parsing. Keep.
- `build_pdf_for_job()` — LaTeX rendering. Keep.
- `_render_letter_tex()` — LaTeX template. Keep.
- `_default_generator()` — Gemini call wrapper. Keep but update.

#### Methods to REWRITE:

##### `create_pre_letter()` — now agent-driven
```python
def create_pre_letter(
    self, job_id: str, source: str = "tu_berlin"
) -> MotivationPreLetterResult:
    """Generate a motivation letter plan using the pre-letter agent.

    Instead of hardcoded keyword matching, the agent analyzes
    the job and profile to produce a section plan with evidence assignments.
    """
    context = self.build_context(job_id=job_id, source=source)
    context_json = json.dumps(context, indent=2, default=str)
    prompt = load_prompt_with_context("motivation_pre_letter", context_json)

    response = self.gemini.generate(prompt)
    plan = json.loads(response)  # Validated by prompt contract

    # Write artifacts
    job_dir = self.config.pipeline_root / source / job_id
    planning_dir = job_dir / "planning"
    planning_dir.mkdir(parents=True, exist_ok=True)

    # Write the plan as JSON (machine-readable)
    plan_path = planning_dir / "motivation_letter.pre.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    # Write a human-readable markdown version
    md_path = planning_dir / "motivation_letter.pre.md"
    md_path.write_text(self._plan_to_markdown(plan, context), encoding="utf-8")

    return MotivationPreLetterResult(
        pre_letter_path=md_path,
        analysis_path=plan_path,
    )
```

##### `generate_for_job()` — inject pre-letter plan into context
```python
def generate_for_job(
    self, job_id: str, source: str = "tu_berlin"
) -> MotivationGenerationResult:
    """Generate the final motivation letter using the LLM agent.

    If a pre-letter plan exists, inject it into the context
    so the agent expands the plan into final prose.
    """
    context = self.build_context(job_id=job_id, source=source)

    # Inject pre-letter plan if it exists
    job_dir = self.config.pipeline_root / source / job_id
    plan_path = job_dir / "planning" / "motivation_letter.pre.json"
    if plan_path.exists():
        context["pre_letter"] = json.loads(plan_path.read_text(encoding="utf-8"))

    context_json = json.dumps(context, indent=2, default=str)
    prompt = load_prompt_with_context("motivation_letter", context_json)

    response = self._generator(prompt)
    result = MotivationLetterOutput.model_validate_json(response)

    # Write outputs
    planning_dir = job_dir / "planning"
    letter_path = planning_dir / "motivation_letter.md"
    letter_path.write_text(result.letter_markdown, encoding="utf-8")

    analysis_path = planning_dir / "motivation_letter.analysis.json"
    analysis_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    return MotivationGenerationResult(
        letter_path=letter_path,
        analysis_path=analysis_path,
    )
```

##### `generate_email_draft()` — now agent-driven
```python
def generate_email_draft(
    self, job_id: str, source: str = "tu_berlin"
) -> MotivationEmailResult:
    """Generate an application email draft using the email agent."""
    context = self.build_context(job_id=job_id, source=source)

    # Slim context for email (doesn't need full evidence catalog)
    email_context = {
        "job": context["job"],
        "candidate": context["candidate"],
    }
    context_json = json.dumps(email_context, indent=2, default=str)
    prompt = load_prompt_with_context("email_draft", context_json)

    response = self.gemini.generate(prompt)
    result = EmailDraftOutput.model_validate_json(response)

    # Write email markdown
    job_dir = self.config.pipeline_root / source / job_id
    planning_dir = job_dir / "planning"
    planning_dir.mkdir(parents=True, exist_ok=True)
    email_path = planning_dir / "application_email.md"

    email_lines = [
        f"To: {result.to}",
        f"Subject: {result.subject}",
        "",
        result.salutation,
        "",
        result.body,
        "",
        result.closing,
        result.sender_name,
        result.sender_email,
        result.sender_phone,
    ]
    email_path.write_text("\n".join(email_lines).strip() + "\n", encoding="utf-8")

    return MotivationEmailResult(email_path=email_path, subject=result.subject)
```

#### New helper method:
```python
def _plan_to_markdown(self, plan: dict, context: dict) -> str:
    """Convert the pre-letter plan JSON to human-readable markdown."""
    lines = ["# Motivation Letter Plan", ""]
    evidence_by_id = {e["id"]: e for e in context.get("evidence_catalog", [])}
    for section, data in plan.get("sections", {}).items():
        lines.append(f"## {section.replace('_', ' ').title()}")
        lines.append(f"**Angle:** {data.get('planning_note', '')}")
        for eid in data.get("evidence_ids", []):
            ev = evidence_by_id.get(eid, {})
            lines.append(f"- [{eid}] {ev.get('text', 'unknown')}")
        lines.append("")
    if plan.get("gaps"):
        lines.append("## Gaps")
        for gap in plan["gaps"]:
            lines.append(f"- **{gap['severity']}**: {gap['requirement']}")
    return "\n".join(lines)
```

### `src/motivation_letter/service.py` — INIT updates
```python
def __init__(self, config=None, generator=None):
    self.config = config or CVConfig.from_defaults()
    self.gemini = GeminiClient()
    self._generator = generator or self._default_generator
    # Remove: self.prompt_path, self.evidence_bank_path as constructor args
    # Prompt loading now goes through src.prompts module
```

## Specification

### What Gets Deleted and Why

| Code | Lines (approx) | Why |
|---|---|---|
| `_build_section_plan()` | 60 lines | Hardcoded keyword sets for section assignment. The pre-letter agent does this semantically. |
| `_render_pre_letter()` | 80 lines | Fixed markdown template with hardcoded section headers. Agent produces the plan. |
| `_select_evidence_ids_by_keywords()` | 20 lines | Helper for deleted scaffold. |
| `_collect_coverage_evidence_ids()` | 15 lines | Helper for deleted scaffold. |
| `_format_evidence_refs()` | 15 lines | Helper for deleted scaffold. |
| `_summarize_requirement_for_email()` | 10 lines | Helper for deleted email. |
| `generate_email_draft()` body | 40 lines | Hardcoded paragraph construction. |
| `PROMPT_RELATIVE_PATH` constant | 1 line | Replaced by prompt loader. |
| `EVIDENCE_BANK_RELATIVE_PATH` constant | 1 line | Evidence bank still used by `build_context()` but path comes from config. |
| **Total** | **~240 lines** | |

### What Stays and Why

| Code | Why keep |
|---|---|
| `build_context()` | Pure data assembly — reads files, builds dict. No creativity needed. |
| `_build_evidence_catalog()` | Creates atomic evidence items from profile. Deterministic, reusable. |
| `_parse_frontmatter()` | YAML parsing utility. |
| `_extract_checklist_items()` | Markdown parsing utility. |
| `build_pdf_for_job()` | LaTeX rendering — deterministic. |
| `_render_letter_tex()` | LaTeX template rendering. |

### Flow Change

**Before:**
```
build_context() → _build_section_plan() [HARDCODED] → _render_pre_letter() [HARDCODED]
    → build_prompt() [template + context] → Gemini → letter
    → generate_email_draft() [HARDCODED]
```

**After:**
```
build_context() → Gemini(motivation_pre_letter prompt) → plan JSON
    → Gemini(motivation_letter prompt + plan) → MotivationLetterOutput
    → Gemini(email_draft prompt) → EmailDraftOutput
```

### Evidence Bank
The evidence bank (`evidence_bank.json`) is currently updated by `create_pre_letter()`. After the rewrite, `build_context()` still reads it, but we no longer update it from the pre-letter step (the agent doesn't produce evidence bank updates). If evidence bank maintenance is needed later, it becomes a separate tool.

## Verification
```bash
cd /home/jp/phd

# 1. Deleted methods don't exist
python -c "
from src.motivation_letter.service import MotivationLetterService
svc = MotivationLetterService()
for name in ['_build_section_plan', '_render_pre_letter', '_select_evidence_ids_by_keywords',
             '_collect_coverage_evidence_ids', '_format_evidence_refs']:
    assert not hasattr(svc, name), f'{name} should be deleted'
print('Hardcoded scaffolding methods deleted.')
"

# 2. Kept methods still exist
python -c "
from src.motivation_letter.service import MotivationLetterService
svc = MotivationLetterService()
for name in ['build_context', '_build_evidence_catalog', 'build_pdf_for_job',
             'create_pre_letter', 'generate_for_job', 'generate_email_draft']:
    assert hasattr(svc, name), f'{name} should exist'
print('Core methods preserved.')
"

# 3. Prompt loading works (no more PROMPT_RELATIVE_PATH)
python -c "
import src.motivation_letter.service as mod
assert not hasattr(mod, 'PROMPT_RELATIVE_PATH'), 'PROMPT_RELATIVE_PATH should be removed'
print('Old prompt path constant removed.')
"

# 4. build_context still works for existing job
python -c "
from src.motivation_letter.service import MotivationLetterService
svc = MotivationLetterService()
try:
    ctx = svc.build_context('201084')
    assert 'job' in ctx
    assert 'candidate' in ctx
    assert 'evidence_catalog' in ctx or 'analysis' in ctx
    print('build_context() works for job 201084.')
except FileNotFoundError:
    print('Job 201084 not found — skipping context test (expected in CI).')
"
```

## Done Criteria
- [ ] `_build_section_plan()` deleted
- [ ] `_render_pre_letter()` deleted
- [ ] All scaffold helper methods deleted
- [ ] `create_pre_letter()` uses `motivation_pre_letter` prompt via Gemini
- [ ] `generate_for_job()` injects pre-letter plan into context if available
- [ ] `generate_email_draft()` uses `email_draft` prompt via Gemini, returns `EmailDraftOutput`
- [ ] `build_context()` unchanged and working
- [ ] `build_pdf_for_job()` unchanged and working
- [ ] `PROMPT_RELATIVE_PATH` constant removed
- [ ] No hardcoded keyword sets remain in the file
- [ ] Verification script exits 0
