# Step 01 — Pydantic Models

## Goal
Create typed Pydantic models for all data flowing through the system: job descriptions, the multi-agent pipeline contract (MATCHER/SELLER/CHECKER), motivation letter I/O, and application plans. These models replace raw dicts and enable Gemini's `response_schema` for structured output.

## Depends on
Nothing — can start immediately.

## Files to Read First
- `src/cv_generator/model.py` — existing `CVModel` dataclass (understand the pattern)
- `src/cv_generator/config.py` — `CVConfig` (understand path resolution)
- `data/reference_data/prompts/Academic_CV_MultiAgent_Pipeline_Prompts.txt` — the JSON contract schema (lines starting with `SHARED JSON CONTRACT`)
- `data/reference_data/prompts/Academic_Motivation_Letter_Prompt.txt` — the output contract (JSON fields: subject, salutation, fit_signals, risk_notes, letter_markdown)
- `src/motivation_letter/service.py` — `MotivationGenerationResult`, `MotivationPreLetterResult`, `MotivationPdfResult`, `MotivationEmailResult` (existing result types to understand)
- `src/scraper/scrape_single_url.py` — `parse_structured_from_markdown()` return shape (what a parsed job looks like)

## Files to Create

### `src/models/__init__.py`
Empty or re-export key models.

### `src/models/job.py`
Job description models parsed from scraper output.

```python
from typing import Literal

from pydantic import BaseModel

class JobRequirement(BaseModel):
    id: str                                    # e.g. "R1"
    text: str
    priority: Literal["must", "nice"] = "must"

class JobPosting(BaseModel):
    title: str
    reference_number: str = ""
    deadline: str = ""
    institution: str = ""
    department: str = ""
    location: str = ""
    contact_name: str = ""
    contact_email: str = ""
    requirements: list[JobRequirement]
    themes: list[str]                          # 5-12 short noun phrases from scope
    responsibilities: list[str] = []
    raw_text: str = ""                         # full markdown for LLM context

    @classmethod
    def from_summary_json(cls, data: dict) -> "JobPosting":
        """Build from scraper's summary.json output."""
        ...
```

### `src/models/pipeline_contract.py`
The shared JSON contract from the multi-agent pipeline prompt. This is the data structure that flows between MATCHER → SELLER → REALITY-CHECKER.

```python
class EvidenceItem(BaseModel):
    id: str                                    # e.g. "E1"
    type: Literal["cv_line", "role", "project", "publication", "education", "skill"]
    text: str
    source_ref: str = ""                       # "CV", "ProfileJSON", "Other"

class RequirementMapping(BaseModel):
    req_id: str
    priority: Literal["must", "nice"]
    coverage: Literal["full", "partial", "none"]
    evidence_ids: list[str]
    notes: str = ""

class ProposedClaim(BaseModel):
    id: str                                    # e.g. "C1"
    target_section: Literal["summary", "experience", "education", "publications", "skills", "languages"]
    target_subsection: str | None = None       # role/org name
    claim_text: str
    based_on_evidence_ids: list[str]
    inflation_level: Literal["none", "light", "high"] = "none"
    risk_level: Literal["low", "medium", "high"] = "low"
    evidence_gap: str = ""
    status: Literal["proposed", "approved", "rejected"] = "proposed"
    reviewer_notes: str = ""

class RenderConfig(BaseModel):
    ordering: list[str] = ["header", "summary", "education", "experience", "publications", "skills", "languages"]
    style_rules: dict[str, bool] = {"one_column": True, "no_tables": True, "no_icons": True}

class PipelineState(BaseModel):
    """Full state object that flows through MATCHER → SELLER → CHECKER."""
    job: JobPosting
    evidence_items: list[EvidenceItem]
    mapping: list[RequirementMapping]
    proposed_claims: list[ProposedClaim] = []
    render: RenderConfig = RenderConfig()
```

### `src/models/motivation.py`
Models for motivation letter generation (replacing the hardcoded scaffold).

```python
class FitSignal(BaseModel):
    requirement: str
    evidence: str
    coverage: Literal["full", "partial"]

class MotivationLetterOutput(BaseModel):
    """Output contract matching the prompt specification."""
    subject: str
    salutation: str
    fit_signals: list[FitSignal]
    risk_notes: list[str] = []
    letter_markdown: str

class EmailDraftOutput(BaseModel):
    """Agent-generated email draft."""
    to: str
    subject: str
    salutation: str
    body: str
    closing: str
    sender_name: str
    sender_email: str = ""
    sender_phone: str = ""
```

### `src/models/application.py`
Top-level models for the orchestrator.

```python
class FitAnalysis(BaseModel):
    """Output of the analyze-fit tool."""
    overall_score: int                         # 0-100
    eligibility: Literal["pass", "risk", "fail"]
    alignment_summary: str
    top_matches: list[FitSignal]
    gaps: list[str]
    recommendation: Literal["strong_apply", "apply", "weak_apply", "skip"]

class ApplicationPlan(BaseModel):
    """One job's application plan within a batch."""
    job: JobPosting
    fit: FitAnalysis
    cv_strategy: str                           # agent's proposed tailoring approach
    motivation_strategy: str                   # agent's proposed letter angle
    priority: int                              # 1=highest

class ApplicationBatch(BaseModel):
    """Output of 'apply-to <urls>' planning phase."""
    plans: list[ApplicationPlan]
    skipped: list[dict]                        # jobs with fit="skip" + reason
```

## Specification

### Design Principles
1. All models inherit from `pydantic.BaseModel` — no dataclasses here (Gemini needs JSON schema)
2. Use `Literal` types for enums to constrain LLM output
3. Default values for optional fields so partial LLM responses don't crash
4. `from_summary_json()` class method on `JobPosting` bridges scraper output → typed model
5. Models are pure data — no business logic, no I/O, no side effects
6. Import path: `from src.models.job import JobPosting`

### Relationship to Existing Code
- `CVModel` in `src/cv_generator/model.py` stays as-is (it's a dataclass used by renderers)
- `PipelineState` replaces the raw dict flowing through `CVMultiAgentPipeline`
- `MotivationLetterOutput` replaces the implicit JSON contract in the motivation prompt
- `JobPosting` will be constructed from scraper output in step 03 (tool extraction)

### Gemini Integration
These models are designed to be passed as `response_schema` to Gemini:
```python
response = client.generate(prompt, response_schema=PipelineState)
state = PipelineState.model_validate_json(response.text)
```

## Verification
```bash
cd /home/jp/phd
python -c "
from src.models.job import JobPosting, JobRequirement
from src.models.pipeline_contract import PipelineState, EvidenceItem, ProposedClaim
from src.models.motivation import MotivationLetterOutput, EmailDraftOutput
from src.models.application import FitAnalysis, ApplicationPlan, ApplicationBatch

# Test JobPosting construction
job = JobPosting(
    title='Research Assistant',
    reference_number='III-51/26',
    requirements=[JobRequirement(id='R1', text='Python experience', priority='must')],
    themes=['workflow orchestration', 'FAIR data'],
)
assert job.reference_number == 'III-51/26'

# Test PipelineState with defaults
state = PipelineState(
    job=job,
    evidence_items=[EvidenceItem(id='E1', type='skill', text='Python 5 years')],
    mapping=[],
)
assert state.render.ordering[0] == 'header'

# Test JSON serialization round-trip
json_str = state.model_dump_json()
state2 = PipelineState.model_validate_json(json_str)
assert state2.job.title == 'Research Assistant'

# Test MotivationLetterOutput
letter = MotivationLetterOutput(
    subject='Application for III-51/26',
    salutation='Dear Prof. Smith,',
    fit_signals=[],
    letter_markdown='test body',
)
assert 'III-51/26' in letter.subject

print('All model tests passed.')
"
```

## Done Criteria
- [ ] `src/models/__init__.py` exists
- [ ] `src/models/job.py` — `JobPosting`, `JobRequirement` importable and constructable
- [ ] `src/models/pipeline_contract.py` — `PipelineState`, `EvidenceItem`, `RequirementMapping`, `ProposedClaim`, `RenderConfig` importable
- [ ] `src/models/motivation.py` — `MotivationLetterOutput`, `EmailDraftOutput`, `FitSignal` importable
- [ ] `src/models/application.py` — `FitAnalysis`, `ApplicationPlan`, `ApplicationBatch` importable
- [ ] All models serialize to JSON and deserialize back without loss
- [ ] Verification script exits 0
