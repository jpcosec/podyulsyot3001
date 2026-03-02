# Step 08 — Task Closure

## Goal
Run the full integration test suite, verify everything works end-to-end, commit all changes, and update documentation. This step is run AFTER all other steps are complete.

## Depends on
All steps (01–07) must be complete.

## Pre-Flight Checks

Before running tests, verify the expected file structure exists:

```bash
cd /home/jp/phd

# Verify new directories exist
ls src/models/__init__.py
ls src/models/job.py
ls src/models/pipeline_contract.py
ls src/models/motivation.py
ls src/models/application.py

ls src/prompts/__init__.py
ls src/prompts/ats_evaluation.txt
ls src/prompts/motivation_letter.txt
ls src/prompts/cv_multi_agent.txt
ls src/prompts/cv_renderer.txt
ls src/prompts/email_draft.txt
ls src/prompts/motivation_pre_letter.txt

ls src/agent/__init__.py
ls src/agent/tools.py
ls src/agent/orchestrator.py
```

## Integration Tests

### Test 1: All Imports Work
```bash
python -c "
# Models
from src.models.job import JobPosting, JobRequirement
from src.models.pipeline_contract import PipelineState, EvidenceItem, ProposedClaim, RequirementMapping, RenderConfig
from src.models.motivation import MotivationLetterOutput, EmailDraftOutput, FitSignal
from src.models.application import FitAnalysis, ApplicationPlan, ApplicationBatch

# Prompts
from src.prompts import load_prompt, load_prompt_with_context

# Agent
from src.agent.tools import scrape_job, analyze_fit, tailor_cv, render_cv, score_ats
from src.agent.tools import plan_motivation_letter, write_motivation_letter, build_motivation_pdf
from src.agent.tools import generate_email_draft, merge_pdfs
from src.agent.orchestrator import ApplicationAgent

# Existing modules still work
from src.cv_generator.config import CVConfig
from src.cv_generator.model import CVModel
from src.cv_generator.pipeline import CVTailoringPipeline
from src.motivation_letter.service import MotivationLetterService
from src.cv_generator.ats import load_ats_prompt
from src.render.docx import DocumentRenderer

print('All imports successful.')
"
```

### Test 2: No Hardcoded Content Remains
```bash
# Check that hardcoded functions are deleted from cli/pipeline.py
python -c "
from src.cli import pipeline as cli

# These should NOT exist
gone = ['render_job_cv_body', 'render_job_cv_main', 'ensure_job_cv_sources', 'CV_RULES']
for name in gone:
    assert not hasattr(cli, name), f'FAIL: {name} still exists in cli/pipeline.py'

print('All hardcoded functions removed from CLI.')
"

# Check motivation letter has no scaffold code
python -c "
from src.motivation_letter.service import MotivationLetterService
svc = MotivationLetterService()
gone = ['_build_section_plan', '_render_pre_letter', '_select_evidence_ids_by_keywords',
        '_collect_coverage_evidence_ids', '_format_evidence_refs']
for name in gone:
    assert not hasattr(svc, name), f'FAIL: {name} still exists in MotivationLetterService'

print('All scaffold methods removed from MotivationLetterService.')
"

# No hardcoded personal data in src/ (except profile JSON which is data)
grep -r "Juan Pablo" src/ --include="*.py" || echo "No hardcoded names in Python files. OK."
grep -r "render_job_cv_body\|render_job_cv_main" src/ --include="*.py" || echo "No references to deleted functions. OK."
```

### Test 3: Prompt Loading Pipeline
```bash
python -c "
from src.prompts import load_prompt, load_prompt_with_context

# All prompts load
for name in ['ats_evaluation', 'cv_multi_agent', 'cv_renderer', 'motivation_letter', 'email_draft', 'motivation_pre_letter']:
    p = load_prompt(name)
    assert len(p) > 100, f'Prompt {name} too short: {len(p)} chars'
    print(f'  {name}: {len(p)} chars OK')

# Context injection works
p = load_prompt_with_context('motivation_letter', '{\"test\": 1}')
assert '{\"test\": 1}' in p
assert '{{CONTEXT_JSON}}' not in p

# ATS module uses new loader
from src.cv_generator.ats import load_ats_prompt
prompt = load_ats_prompt()
assert 'Academic Pre-Screening' in prompt

print('Prompt loading pipeline works.')
"
```

### Test 4: Pydantic Model Round-Trips
```bash
python -c "
from src.models.job import JobPosting, JobRequirement
from src.models.pipeline_contract import PipelineState, EvidenceItem, RequirementMapping
from src.models.motivation import MotivationLetterOutput
from src.models.application import FitAnalysis, ApplicationPlan, ApplicationBatch

# Build a complete pipeline state
job = JobPosting(
    title='Research Assistant',
    reference_number='III-51/26',
    requirements=[
        JobRequirement(id='R1', text='Python', priority='must'),
        JobRequirement(id='R2', text='Docker', priority='nice'),
    ],
    themes=['MLOps', 'FAIR data'],
)
state = PipelineState(
    job=job,
    evidence_items=[EvidenceItem(id='E1', type='skill', text='Python 5y')],
    mapping=[RequirementMapping(req_id='R1', priority='must', coverage='full', evidence_ids=['E1'])],
)

# Round-trip
json_str = state.model_dump_json()
state2 = PipelineState.model_validate_json(json_str)
assert state2.job.title == 'Research Assistant'
assert state2.mapping[0].coverage == 'full'

# Motivation output
letter = MotivationLetterOutput(
    subject='Application for III-51/26',
    salutation='Dear Prof. Smith,',
    fit_signals=[],
    letter_markdown='body text',
)
assert letter.model_dump_json()

# Application batch
fit = FitAnalysis(
    overall_score=75,
    eligibility='pass',
    alignment_summary='Strong Python match',
    top_matches=[],
    gaps=['Docker experience'],
    recommendation='apply',
)
plan = ApplicationPlan(job=job, fit=fit, cv_strategy='Emphasize Python', motivation_strategy='', priority=1)
batch = ApplicationBatch(plans=[plan], skipped=[])
assert len(batch.plans) == 1

print('All model round-trips pass.')
"
```

### Test 5: CLI Parser
```bash
python -c "
from src.cli.pipeline import build_parser

parser = build_parser()

# apply-to command works
args = parser.parse_args(['apply-to', 'https://example.com/job1', '--auto'])
assert args.command == 'apply-to'
assert args.urls == ['https://example.com/job1']
assert args.auto == True

# Existing commands still work
args = parser.parse_args(['cv-build', '201084', 'english', '--via', 'docx'])
assert args.command == 'cv-build'

args = parser.parse_args(['status'])
assert args.command == 'status'

print('CLI parser works for all commands.')
"
```

### Test 6: Existing Tests Still Pass
```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```

### Test 7: AST.md Deleted
```bash
python -c "
from pathlib import Path
assert not Path('data/reference_data/prompts/AST.md').exists(), 'AST.md should be deleted'
print('AST.md deleted.')
"
```

## Post-Test Actions

### Update Changelog
Add entry to `changelog.md`:

```markdown
## 2026-03-02 — De-hardcode Pipeline & Agent Architecture

### Added
- `src/models/` — Pydantic models for job postings, pipeline contract, motivation letters, and application plans
- `src/prompts/` — Centralized prompt files with loader utility (moved from data/reference_data/prompts/)
- `src/agent/tools.py` — Tool functions wrapping scraper, renderer, ATS, and motivation services
- `src/agent/orchestrator.py` — `ApplicationAgent` for batch application processing
- `apply-to <urls>` CLI command — guided application workflow with human-in-the-loop checkpoints
- `src/prompts/email_draft.txt` — Agent prompt for email generation
- `src/prompts/motivation_pre_letter.txt` — Agent prompt for motivation letter planning

### Changed
- `src/cv_generator/pipeline.py` — Rewritten as `CVTailoringPipeline` using full prompts from files + Pydantic models
- `src/motivation_letter/service.py` — Rebuilt as agent-driven (pre-letter plan + generation + email all via LLM)
- `src/cv_generator/ats.py` — Uses `src/prompts/` loader instead of hardcoded path

### Removed
- `CV_RULES` constant from `src/cli/pipeline.py` — replaced by MATCHER agent
- `render_job_cv_body()`, `render_job_cv_main()`, `ensure_job_cv_sources()` — hardcoded LaTeX content
- `build_cv_tailoring()` hardcoded logic — now delegates to `CVTailoringPipeline`
- `_build_section_plan()`, `_render_pre_letter()` and helper methods from `MotivationLetterService` — replaced by pre-letter agent
- Hardcoded email draft template from `generate_email_draft()` — replaced by email agent
- `data/reference_data/prompts/AST.md` — duplicate of ATS prompt
```

### Commit
```bash
cd /home/jp/phd

# Stage all new and modified files
git add src/models/
git add src/prompts/
git add src/agent/
git add src/cv_generator/pipeline.py
git add src/cv_generator/ats.py
git add src/motivation_letter/service.py
git add src/cli/pipeline.py
git add docs/plans/2026-03-02-de-hardcode-agent-architecture/
git add changelog.md

# Stage deletion
git rm data/reference_data/prompts/AST.md

# Verify what's staged
git diff --cached --stat

# Commit
git commit -m "$(cat <<'EOF'
De-hardcode pipeline and build agent orchestration architecture

Replace hardcoded CV tailoring (CV_RULES, LaTeX body/header) and
motivation letter scaffolding with LLM agent-driven generation.

- Add Pydantic models for typed data flow (job, pipeline, motivation)
- Move prompts to src/prompts/ with loader utility
- Rebuild CVMultiAgentPipeline with full prompts + structured output
- Rebuild MotivationLetterService as fully agent-driven
- Add tool functions wrapping scraper/renderer/ATS/motivation
- Add ApplicationAgent orchestrator for batch processing
- Add 'apply-to <urls>' CLI command with human checkpoints
- Delete ~470 lines of hardcoded content

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Verify Commit
```bash
git log -1 --stat
git status
```

## Done Criteria
- [ ] Test 1: All imports pass
- [ ] Test 2: No hardcoded content remains
- [ ] Test 3: Prompt loading works
- [ ] Test 4: Pydantic models round-trip
- [ ] Test 5: CLI parser works
- [ ] Test 6: Existing tests still pass
- [ ] Test 7: AST.md deleted
- [ ] Changelog updated
- [ ] Changes committed
- [ ] `git status` clean
