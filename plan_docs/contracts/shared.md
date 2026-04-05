# Shared Contracts

Date: 2026-04-05
Status: design-only (current contracts exist in `src/apply/models.py`, `src/scraper/models.py`)

## Purpose

Contracts that cross multiple boundaries — used by motors, portals, the CLI,
and Ariadne. These are not owned by any single component.

## Execution result contracts

### ExecutionResult

Unified outcome of any motor execution (apply or scrape).

```python
class ExecutionResult(BaseModel):
    source: str
    job_id: str
    motor: str                       # "crawl4ai", "browseros_cli", "os_native", etc.
    status: ExecutionStatus
    timestamp: str
    fields_filled: list[str] = []
    confirmation_text: str | None = None
    error: str | None = None
    artifacts: ExecutionArtifacts
```

### ExecutionStatus

```python
ExecutionStatus = Literal[
    "submitted",       # application sent
    "dry_run",         # stopped before submit
    "failed",          # execution error
    "portal_changed",  # structural drift detected
    "aborted",         # operator or timeout stopped execution
]
```

**Current equivalent:** `ApplyMeta.status` in `src/apply/models.py` (same values
minus `aborted`).

### ExecutionArtifacts

References to artifacts produced during execution.

```python
class ExecutionArtifacts(BaseModel):
    screenshot: str | None = None           # pre-submit screenshot path
    screenshot_submitted: str | None = None # post-submit screenshot path
    screenshot_error: str | None = None     # error-state screenshot path
    application_record: str | None = None   # application record path
    replay_meta: str | None = None          # Ariadne replay metadata path
```

## Application record

### ApplicationRecord

Persisted record of one apply attempt. Used for audit and debugging.

```python
class ApplicationRecord(BaseModel):
    source: str
    job_id: str
    job_title: str
    company_name: str
    application_url: str
    motor: str                       # which motor executed this
    cv_path: str
    letter_path: str | None = None
    fields_filled: list[str]
    dry_run: bool
    submitted_at: str | None = None
    confirmation_text: str | None = None
    ariadne_path_id: str | None = None    # which Ariadne path was used
    ariadne_path_version: str | None = None
```

**Current equivalent:** `ApplicationRecord` in `src/apply/models.py` (same fields
minus `motor`, `ariadne_path_id`, `ariadne_path_version`).

## Job data contracts

### JobPosting

Standardized job posting extracted by the scraper. This is the existing contract
that feeds the entire downstream pipeline.

```python
class JobPosting(BaseModel):
    # Mandatory
    job_title: str
    company_name: str
    location: str
    employment_type: str
    responsibilities: list[str]      # min 1 item
    requirements: list[str]          # min 1 item

    # Optional
    salary: str | None = None
    remote_policy: str | None = None
    benefits: list[str] = []
    company_description: str | None = None
    company_industry: str | None = None
    company_size: str | None = None
    posted_date: str | None = None
    days_ago: str | None = None
    application_deadline: str | None = None
    application_method: str | None = None
    application_url: str | None = None
    application_email: str | None = None
    application_instructions: str | None = None
    reference_number: str | None = None
    contact_info: str | None = None
    original_language: str | None = None
```

**Current location:** `src/scraper/models.py` — no changes needed, this contract
is stable and well-tested.

### IngestArtifact

The subset of job data that downstream stages consume. Currently read as a raw
dict from `state.json` — should be a typed contract.

```python
class IngestArtifact(BaseModel):
    job_title: str
    company_name: str
    application_url: str | None = None
    url: str | None = None           # fallback if application_url is absent
    application_method: str | None = None
    original_language: str | None = None
    listing_case: dict | None = None
```

**Current equivalent:** raw `dict` loaded from `state.json` via
`DataManager.read_json_artifact()`. Both `ApplyAdapter._read_ingest_artifact()`
and `BrowserOSApplyProvider._read_ingest_artifact()` read it as an untyped dict.

## Profile contracts

### CandidateProfile

Candidate personal data used for form filling and template substitution.

```python
class CandidateProfile(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    phone_country_code: str | None = None
```

**Current equivalent:** raw `dict` passed via `--profile-json` CLI flag,
consumed as `self.candidate_profile` in `BrowserOSApplyProvider._build_context()`.
The Crawl4AI apply adapters don't use a profile contract at all — `ApplyAdapter._build_profile()`
returns only job-level fields and has a TODO for candidate fields.

### ExecutionContext

The full context dict used for `{{placeholder}}` resolution in Ariadne paths
and motor execution plans.

```python
class ExecutionContext(BaseModel):
    profile: CandidateProfile
    job: IngestArtifact
    cv_path: str
    cv_filename: str
    letter_path: str | None = None
```

**Current equivalent:** `BrowserOSApplyProvider._build_context()` return dict
and `ApplyAdapter._build_profile()` return dict. Currently two different shapes —
this contract unifies them.

## Scrape metadata

### ScrapeMeta

Metadata about a scraping run for one job.

```python
class ScrapeMeta(BaseModel):
    timestamp: str
    job_id: str
    url: str
    success: bool
    extraction_method: Literal["css", "llm", "none"]
    error: str | None = None
    crawl_stats: dict = {}
    response_status: int | None = None
```

**Current equivalent:** dict returned by `SmartScraperAdapter._meta_log()` in
`src/scraper/smart_adapter.py`. Same fields, currently untyped.

## Migration from current contracts

| Current contract | Location | Target |
|---|---|---|
| `FormSelectors` | `src/apply/models.py` | Replaced by `PortalApplyFlow.form_targets` (dict of AriadneTarget) |
| `ApplicationRecord` | `src/apply/models.py` | `shared.ApplicationRecord` (add motor, ariadne fields) |
| `ApplyMeta` | `src/apply/models.py` | `shared.ExecutionResult` (generalized) |
| `JobPosting` | `src/scraper/models.py` | Unchanged — stable contract |
| `BrowserOSPlaybook` | `src/apply/browseros_models.py` | Split: `AriadnePath` (Ariadne) + `BrowserOSCliPlan` (motor) |
| `PlaybookStep` etc. | `src/apply/browseros_models.py` | Split: `AriadneStep` (Ariadne) + `BrowserOSCliStep` (motor) |
| `_build_context()` return | `src/apply/browseros_backend.py` | `shared.ExecutionContext` |
| `_build_profile()` return | `src/apply/smart_adapter.py` | `shared.ExecutionContext` |
| `_meta_log()` return | `src/scraper/smart_adapter.py` | `shared.ScrapeMeta` |
| ingest `state.json` dict | (untyped) | `shared.IngestArtifact` |

## Open questions

1. Should `ExecutionResult` carry the full `ApplicationRecord` or just a
   reference to the file path? Carrying the full record is convenient but
   makes the result object heavy.
2. Should `CandidateProfile` support additional fields beyond the basics
   (salary expectation, start date, work authorization, etc.)? These appear
   in some portal forms but are not universal.
3. Should `IngestArtifact` be a strict subset of `JobPosting`, or can it
   carry additional fields (like `listing_case`) that `JobPosting` doesn't?
4. Should there be a `PortalSession` contract representing an authenticated
   session (cookie state, profile dir, token expiry) that motors check before
   execution?
