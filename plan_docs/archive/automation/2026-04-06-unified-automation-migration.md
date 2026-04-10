# Unified Automation Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all automation code under `src/automation/` with a clean Ariadne portal schema as the boundary between portal knowledge and motor execution.

**Architecture:** Define minimal Ariadne portal models first, write portal intent files against them, rewrite C4AI portal adapters to consume portal intent, then do the structural move of all remaining code. Old `src/scraper/` and `src/apply/` are deleted at the end.

**Tech Stack:** Python 3.11+, Pydantic v2, Crawl4AI, BrowserOS MCP, pytest

---

## Task 1: Scaffold `src/automation/` package tree and update sparse checkout

**Files:**
- Create: `src/automation/__init__.py`
- Create: `src/automation/ariadne/__init__.py`
- Create: `src/automation/portals/__init__.py`
- Create: `src/automation/portals/stepstone/__init__.py`
- Create: `src/automation/portals/xing/__init__.py`
- Create: `src/automation/portals/tuberlin/__init__.py`
- Create: `src/automation/portals/linkedin/__init__.py`
- Create: `src/automation/motors/__init__.py`
- Create: `src/automation/motors/crawl4ai/__init__.py`
- Create: `src/automation/motors/crawl4ai/portals/__init__.py`
- Create: `src/automation/motors/crawl4ai/portals/stepstone/__init__.py`
- Create: `src/automation/motors/crawl4ai/portals/xing/__init__.py`
- Create: `src/automation/motors/crawl4ai/portals/tuberlin/__init__.py`
- Create: `src/automation/motors/crawl4ai/portals/linkedin/__init__.py`
- Create: `src/automation/motors/browseros/__init__.py`
- Create: `src/automation/motors/browseros/cli/__init__.py`
- Create: `src/automation/motors/browseros/cli/traces/.gitkeep`
- Create: `tests/unit/automation/__init__.py`
- Create: `tests/unit/automation/ariadne/__init__.py`
- Create: `tests/unit/automation/portals/__init__.py`
- Create: `tests/unit/automation/motors/__init__.py`
- Create: `tests/unit/automation/motors/crawl4ai/__init__.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/__init__.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/stepstone/__init__.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/xing/__init__.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/tuberlin/__init__.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/linkedin/__init__.py`
- Create: `tests/unit/automation/motors/browseros/__init__.py`
- Create: `tests/unit/automation/motors/browseros/cli/__init__.py`

- [ ] **Step 1: Create all `__init__.py` files**

```bash
# Run from worktree root
python - <<'EOF'
import pathlib
dirs = [
    "src/automation",
    "src/automation/ariadne",
    "src/automation/portals",
    "src/automation/portals/stepstone",
    "src/automation/portals/xing",
    "src/automation/portals/tuberlin",
    "src/automation/portals/linkedin",
    "src/automation/motors",
    "src/automation/motors/crawl4ai",
    "src/automation/motors/crawl4ai/portals",
    "src/automation/motors/crawl4ai/portals/stepstone",
    "src/automation/motors/crawl4ai/portals/xing",
    "src/automation/motors/crawl4ai/portals/tuberlin",
    "src/automation/motors/crawl4ai/portals/linkedin",
    "src/automation/motors/crawl4ai/schemas",
    "src/automation/motors/browseros",
    "src/automation/motors/browseros/cli",
    "src/automation/motors/browseros/cli/traces",
    "tests/unit/automation",
    "tests/unit/automation/ariadne",
    "tests/unit/automation/portals",
    "tests/unit/automation/motors",
    "tests/unit/automation/motors/crawl4ai",
    "tests/unit/automation/motors/crawl4ai/portals",
    "tests/unit/automation/motors/crawl4ai/portals/stepstone",
    "tests/unit/automation/motors/crawl4ai/portals/xing",
    "tests/unit/automation/motors/crawl4ai/portals/tuberlin",
    "tests/unit/automation/motors/crawl4ai/portals/linkedin",
    "tests/unit/automation/motors/browseros",
    "tests/unit/automation/motors/browseros/cli",
]
for d in dirs:
    p = pathlib.Path(d)
    p.mkdir(parents=True, exist_ok=True)
    init = p / "__init__.py"
    if not init.exists():
        init.write_text("")
pathlib.Path("src/automation/motors/browseros/cli/traces/.gitkeep").touch()
print("Done")
EOF
```

Expected: `Done`

- [ ] **Step 2: Add new paths to sparse checkout**

```bash
git sparse-checkout add \
  src/automation \
  tests/unit/automation \
  docs/superpowers
```

Expected: no errors (warnings about other paths are ok)

- [ ] **Step 3: Verify Python can import the empty packages**

```bash
python -c "import src.automation; import src.automation.ariadne; import src.automation.motors.crawl4ai; import src.automation.motors.browseros.cli; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/automation/ tests/unit/automation/
git commit -m "chore: scaffold src/automation package tree"
```

---

## Task 2: Define Ariadne portal schema

**Files:**
- Create: `src/automation/ariadne/portal_models.py`
- Create: `tests/unit/automation/ariadne/test_portal_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/ariadne/test_portal_models.py
"""Tests for Ariadne portal schema models."""
from __future__ import annotations

import pytest

from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
    ScrapePortalDefinition,
)


def test_field_type_values():
    assert FieldType.TEXT == "text"
    assert FieldType.EMAIL == "email"
    assert FieldType.PHONE == "phone"
    assert FieldType.FILE_PDF == "file_pdf"


def test_form_field_required_fields():
    field = FormField(
        name="first_name",
        label="First name",
        required=False,
        field_type=FieldType.TEXT,
    )
    assert field.name == "first_name"
    assert field.required is False


def test_apply_step_defaults():
    step = ApplyStep(name="submit", description="Submit the form", fields=[])
    assert step.dry_run_stop is False


def test_apply_step_dry_run_stop():
    step = ApplyStep(
        name="submit", description="Submit the form", fields=[], dry_run_stop=True
    )
    assert step.dry_run_stop is True


def test_apply_portal_definition_round_trip():
    defn = ApplyPortalDefinition(
        source_name="testportal",
        base_url="https://test.example.com",
        entry_description="Test apply modal",
        steps=[
            ApplyStep(
                name="fill",
                description="Fill form",
                fields=[
                    FormField(
                        name="cv",
                        label="CV",
                        required=True,
                        field_type=FieldType.FILE_PDF,
                    )
                ],
            )
        ],
    )
    assert defn.source_name == "testportal"
    assert defn.steps[0].fields[0].required is True


def test_scrape_portal_definition():
    defn = ScrapePortalDefinition(
        source_name="testportal",
        base_url="https://test.example.com",
        supported_params=["job_query", "city"],
        job_id_pattern=r"-(\d+)$",
    )
    assert "job_query" in defn.supported_params
    assert defn.job_id_pattern == r"-(\d+)$"


def test_scrape_portal_job_id_pattern_is_valid_regex():
    import re

    defn = ScrapePortalDefinition(
        source_name="testportal",
        base_url="https://test.example.com",
        supported_params=[],
        job_id_pattern=r"-(\d+)$",
    )
    match = re.search(defn.job_id_pattern, "https://example.com/jobs/engineer-12345")
    assert match is not None
    assert match.group(1) == "12345"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/ariadne/test_portal_models.py -v
```

Expected: `ImportError` — `portal_models` module not found

- [ ] **Step 3: Write the implementation**

```python
# src/automation/ariadne/portal_models.py
"""Ariadne portal schema — motor-agnostic portal intent models.

These models express WHAT a portal offers and expects. Motors translate
these definitions into their own execution language (CSS selectors,
C4A-Script, BrowserOS tool calls, etc.).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    FILE_PDF = "file_pdf"


class FormField(BaseModel):
    """One form field in motor-agnostic terms."""

    name: str
    label: str
    required: bool
    field_type: FieldType


class ApplyStep(BaseModel):
    """One step in an application flow, motor-agnostic."""

    name: str
    description: str
    fields: list[FormField]
    dry_run_stop: bool = False


class ApplyPortalDefinition(BaseModel):
    """Motor-agnostic description of a portal's apply flow."""

    source_name: str
    base_url: str
    entry_description: str
    steps: list[ApplyStep]


class ScrapePortalDefinition(BaseModel):
    """Motor-agnostic description of a portal's scrape interface."""

    source_name: str
    base_url: str
    supported_params: list[str]
    job_id_pattern: str
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/ariadne/test_portal_models.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/ariadne/portal_models.py tests/unit/automation/ariadne/test_portal_models.py
git commit -m "feat(ariadne): add portal schema models — ScrapePortalDefinition, ApplyPortalDefinition"
```

---

## Task 3: Write portal intent files for scraping

**Files:**
- Create: `src/automation/portals/stepstone/scrape.py`
- Create: `src/automation/portals/xing/scrape.py`
- Create: `src/automation/portals/tuberlin/scrape.py`
- Create: `tests/unit/automation/portals/test_scrape_portals.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/portals/test_scrape_portals.py
"""Tests that scrape portal definitions are valid and contain expected data."""
from __future__ import annotations

import re

import pytest

from src.automation.ariadne.portal_models import ScrapePortalDefinition


def _assert_valid_regex(pattern: str, sample_url: str, expected_id: str) -> None:
    match = re.search(pattern, sample_url)
    assert match is not None, f"Pattern {pattern!r} did not match {sample_url!r}"
    assert match.group(1) == expected_id


def test_stepstone_scrape_portal():
    from src.automation.portals.stepstone.scrape import STEPSTONE_SCRAPE

    assert isinstance(STEPSTONE_SCRAPE, ScrapePortalDefinition)
    assert STEPSTONE_SCRAPE.source_name == "stepstone"
    assert STEPSTONE_SCRAPE.base_url == "https://www.stepstone.de"
    assert "job_query" in STEPSTONE_SCRAPE.supported_params
    assert "city" in STEPSTONE_SCRAPE.supported_params
    assert "max_days" in STEPSTONE_SCRAPE.supported_params
    _assert_valid_regex(
        STEPSTONE_SCRAPE.job_id_pattern,
        "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html",
        "12345678",
    )


def test_xing_scrape_portal():
    from src.automation.portals.xing.scrape import XING_SCRAPE

    assert isinstance(XING_SCRAPE, ScrapePortalDefinition)
    assert XING_SCRAPE.source_name == "xing"
    assert XING_SCRAPE.base_url == "https://www.xing.com"
    assert "job_query" in XING_SCRAPE.supported_params
    _assert_valid_regex(
        XING_SCRAPE.job_id_pattern,
        "https://www.xing.com/jobs/berlin-data-engineer-9876543",
        "9876543",
    )


def test_tuberlin_scrape_portal():
    from src.automation.portals.tuberlin.scrape import TUBERLIN_SCRAPE

    assert isinstance(TUBERLIN_SCRAPE, ScrapePortalDefinition)
    assert TUBERLIN_SCRAPE.source_name == "tuberlin"
    assert TUBERLIN_SCRAPE.base_url == "https://www.jobs.tu-berlin.de"
    assert "categories" in TUBERLIN_SCRAPE.supported_params
    assert "job_query" in TUBERLIN_SCRAPE.supported_params
    _assert_valid_regex(
        TUBERLIN_SCRAPE.job_id_pattern,
        "https://www.jobs.tu-berlin.de/en/job-postings/11223344",
        "11223344",
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/portals/test_scrape_portals.py -v
```

Expected: `ImportError` — portal modules not found

- [ ] **Step 3: Write the three portal intent files**

```python
# src/automation/portals/stepstone/scrape.py
"""StepStone scrape portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import ScrapePortalDefinition

STEPSTONE_SCRAPE = ScrapePortalDefinition(
    source_name="stepstone",
    base_url="https://www.stepstone.de",
    supported_params=["job_query", "city", "max_days"],
    job_id_pattern=r"--(\d+)-inline\.html",
)
```

```python
# src/automation/portals/xing/scrape.py
"""XING scrape portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import ScrapePortalDefinition

XING_SCRAPE = ScrapePortalDefinition(
    source_name="xing",
    base_url="https://www.xing.com",
    supported_params=["job_query", "city", "max_days"],
    job_id_pattern=r"-(\d+)$",
)
```

```python
# src/automation/portals/tuberlin/scrape.py
"""TU Berlin scrape portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import ScrapePortalDefinition

TUBERLIN_SCRAPE = ScrapePortalDefinition(
    source_name="tuberlin",
    base_url="https://www.jobs.tu-berlin.de",
    supported_params=["categories", "job_query"],
    job_id_pattern=r"/job-postings/(\d+)",
)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/portals/test_scrape_portals.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/portals/ tests/unit/automation/portals/test_scrape_portals.py
git commit -m "feat(portals): add scrape portal definitions for stepstone, xing, tuberlin"
```

---

## Task 4: Write portal intent files for applying

**Files:**
- Create: `src/automation/portals/linkedin/apply.py`
- Create: `src/automation/portals/stepstone/apply.py`
- Create: `src/automation/portals/xing/apply.py`
- Create: `tests/unit/automation/portals/test_apply_portals.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/portals/test_apply_portals.py
"""Tests that apply portal definitions are valid and contain expected data."""
from __future__ import annotations

from src.automation.ariadne.portal_models import ApplyPortalDefinition, FieldType


def _get_field(defn: ApplyPortalDefinition, step_name: str, field_name: str):
    step = next(s for s in defn.steps if s.name == step_name)
    return next(f for f in step.fields if f.name == field_name)


def test_linkedin_apply_portal():
    from src.automation.portals.linkedin.apply import LINKEDIN_APPLY

    assert isinstance(LINKEDIN_APPLY, ApplyPortalDefinition)
    assert LINKEDIN_APPLY.source_name == "linkedin"
    assert LINKEDIN_APPLY.base_url == "https://www.linkedin.com"
    step_names = [s.name for s in LINKEDIN_APPLY.steps]
    assert "open_modal" in step_names
    assert "upload_cv" in step_names
    assert "submit" in step_names
    cv_field = _get_field(LINKEDIN_APPLY, "upload_cv", "cv")
    assert cv_field.field_type == FieldType.FILE_PDF
    assert cv_field.required is True
    submit_step = next(s for s in LINKEDIN_APPLY.steps if s.name == "submit")
    assert submit_step.dry_run_stop is True


def test_stepstone_apply_portal():
    from src.automation.portals.stepstone.apply import STEPSTONE_APPLY

    assert isinstance(STEPSTONE_APPLY, ApplyPortalDefinition)
    assert STEPSTONE_APPLY.source_name == "stepstone"
    assert STEPSTONE_APPLY.base_url == "https://www.stepstone.de"
    step_names = [s.name for s in STEPSTONE_APPLY.steps]
    assert "submit" in step_names
    submit_step = next(s for s in STEPSTONE_APPLY.steps if s.name == "submit")
    assert submit_step.dry_run_stop is True


def test_xing_apply_portal():
    from src.automation.portals.xing.apply import XING_APPLY

    assert isinstance(XING_APPLY, ApplyPortalDefinition)
    assert XING_APPLY.source_name == "xing"
    assert XING_APPLY.base_url == "https://www.xing.com"
    step_names = [s.name for s in XING_APPLY.steps]
    assert "submit" in step_names
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/portals/test_apply_portals.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write the three portal intent files**

```python
# src/automation/portals/linkedin/apply.py
"""LinkedIn apply portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
)

LINKEDIN_APPLY = ApplyPortalDefinition(
    source_name="linkedin",
    base_url="https://www.linkedin.com",
    entry_description="LinkedIn Easy Apply modal triggered by the 'Easy Apply' button on job listings",
    steps=[
        ApplyStep(name="open_modal", description="Open the LinkedIn Easy Apply modal", fields=[]),
        ApplyStep(
            name="fill_contact",
            description="Fill contact information fields",
            fields=[
                FormField(name="first_name", label="First name", required=False, field_type=FieldType.TEXT),
                FormField(name="last_name", label="Last name", required=False, field_type=FieldType.TEXT),
                FormField(name="email", label="Email", required=False, field_type=FieldType.EMAIL),
                FormField(name="phone", label="Phone", required=False, field_type=FieldType.PHONE),
            ],
        ),
        ApplyStep(
            name="upload_cv",
            description="Select or upload CV document",
            fields=[
                FormField(name="cv", label="CV / Resume", required=True, field_type=FieldType.FILE_PDF),
            ],
        ),
        ApplyStep(name="submit", description="Submit the application", fields=[], dry_run_stop=True),
    ],
)
```

```python
# src/automation/portals/stepstone/apply.py
"""StepStone apply portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
)

STEPSTONE_APPLY = ApplyPortalDefinition(
    source_name="stepstone",
    base_url="https://www.stepstone.de",
    entry_description="StepStone Easy Apply modal triggered by the apply button on job listings",
    steps=[
        ApplyStep(name="open_modal", description="Open the StepStone Easy Apply modal", fields=[]),
        ApplyStep(
            name="fill_contact",
            description="Fill contact information fields",
            fields=[
                FormField(name="first_name", label="First name", required=False, field_type=FieldType.TEXT),
                FormField(name="last_name", label="Last name", required=False, field_type=FieldType.TEXT),
                FormField(name="email", label="Email", required=False, field_type=FieldType.EMAIL),
                FormField(name="phone", label="Phone", required=False, field_type=FieldType.PHONE),
            ],
        ),
        ApplyStep(
            name="upload_cv",
            description="Upload CV document",
            fields=[
                FormField(name="cv", label="CV / Resume", required=True, field_type=FieldType.FILE_PDF),
            ],
        ),
        ApplyStep(name="submit", description="Submit the application", fields=[], dry_run_stop=True),
    ],
)
```

```python
# src/automation/portals/xing/apply.py
"""XING apply portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
)

XING_APPLY = ApplyPortalDefinition(
    source_name="xing",
    base_url="https://www.xing.com",
    entry_description="XING Easy Apply modal triggered by the apply button on job listings",
    steps=[
        ApplyStep(name="open_modal", description="Open the XING Easy Apply modal", fields=[]),
        ApplyStep(
            name="fill_contact",
            description="Fill contact information fields",
            fields=[
                FormField(name="first_name", label="First name", required=False, field_type=FieldType.TEXT),
                FormField(name="last_name", label="Last name", required=False, field_type=FieldType.TEXT),
                FormField(name="email", label="Email", required=False, field_type=FieldType.EMAIL),
                FormField(name="phone", label="Phone", required=False, field_type=FieldType.PHONE),
            ],
        ),
        ApplyStep(
            name="upload_cv",
            description="Upload CV document",
            fields=[
                FormField(name="cv", label="CV / Resume", required=True, field_type=FieldType.FILE_PDF),
            ],
        ),
        ApplyStep(name="submit", description="Submit the application", fields=[], dry_run_stop=True),
    ],
)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/portals/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/portals/ tests/unit/automation/portals/test_apply_portals.py
git commit -m "feat(portals): add apply portal definitions for linkedin, stepstone, xing"
```

---

## Task 5: Merge and move C4AI models

Merge `src/scraper/models.py` (`JobPosting`) and `src/apply/models.py` (`FormSelectors`, `ApplicationRecord`, `ApplyMeta`) into `src/automation/motors/crawl4ai/models.py`. Move the models tests. The CLI parser tests from `test_models.py` move to a separate file in Task 12.

**Files:**
- Create: `src/automation/motors/crawl4ai/models.py`
- Create: `tests/unit/automation/motors/crawl4ai/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/automation/motors/crawl4ai/test_models.py` — copy `tests/unit/apply/test_models.py`, update the imports, and remove the `build_parser` tests (those belong with the CLI):

```python
# tests/unit/automation/motors/crawl4ai/test_models.py
"""Tests for C4AI motor models."""
from __future__ import annotations

import pytest

from src.automation.motors.crawl4ai.models import (
    ApplicationRecord,
    ApplyMeta,
    FormSelectors,
    JobPosting,
)


def test_job_posting_requires_mandatory_fields():
    with pytest.raises(Exception):
        JobPosting()

    posting = JobPosting(
        job_title="Data Engineer",
        company_name="Acme GmbH",
        location="Berlin",
        employment_type="Full-time",
        responsibilities=["Build pipelines"],
        requirements=["Python"],
    )
    assert posting.job_title == "Data Engineer"
    assert posting.salary is None


def test_form_selectors_mandatory_fields_required():
    with pytest.raises(Exception):
        FormSelectors()

    sel = FormSelectors(
        apply_button="button[data-testid='apply']",
        cv_upload="input[type='file']",
        submit_button="button[type='submit']",
        success_indicator=".application-success",
    )
    assert sel.first_name is None
    assert sel.cv_select_existing is None


def test_form_selectors_optional_fields():
    sel = FormSelectors(
        apply_button="button",
        cv_upload="input",
        submit_button="button",
        success_indicator=".success",
        first_name="input[name='firstName']",
        cv_select_existing="button.select-cv",
    )
    assert sel.first_name == "input[name='firstName']"
    assert sel.last_name is None


def test_apply_meta_status_values():
    for status in ("submitted", "dry_run", "failed", "portal_changed"):
        m = ApplyMeta(status=status, timestamp="2026-03-30T00:00:00Z")
        assert m.status == status

    with pytest.raises(Exception):
        ApplyMeta(status="unknown", timestamp="2026-03-30T00:00:00Z")


def test_apply_meta_serialization():
    m = ApplyMeta(status="submitted", timestamp="2026-03-30T00:00:00Z")
    d = m.model_dump()
    assert d["status"] == "submitted"
    assert d["error"] is None


def test_application_record_round_trip():
    rec = ApplicationRecord(
        source="xing",
        job_id="12345",
        job_title="Data Engineer",
        company_name="Acme GmbH",
        application_url="https://xing.com/jobs/data-engineer-12345",
        cv_path="/path/to/cv.pdf",
        letter_path=None,
        fields_filled=["first_name", "last_name", "email"],
        dry_run=False,
        submitted_at="2026-03-30T00:00:00Z",
        confirmation_text="Your application was received.",
    )
    d = rec.model_dump()
    assert d["source"] == "xing"
    assert d["letter_path"] is None
    assert d["dry_run"] is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_models.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create the merged models file**

```python
# src/automation/motors/crawl4ai/models.py
"""C4AI motor data contracts.

Scrape-side: JobPosting — structured extraction output from a scrape run.
Apply-side:  FormSelectors, ApplicationRecord, ApplyMeta — apply flow I/O.

Both live here because they are produced and consumed exclusively within
the Crawl4AI motor.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ── Scrape side ──────────────────────────────────────────────────────────────

class JobPosting(BaseModel):
    """Standardized extraction output contract for all scraping sources."""

    # Mandatory
    job_title: str = Field(..., description="The official job title")
    company_name: str = Field(..., description="Name of the company, university, or institution")
    location: str = Field(..., description="City or primary location")
    employment_type: str = Field(..., description="Type of employment (e.g. Full-time, Part-time, Internship)")
    responsibilities: List[str] = Field(..., min_length=1, description="List of responsibilities or tasks")
    requirements: List[str] = Field(..., min_length=1, description="List of requirements, profile or skills")

    # Optional
    salary: Optional[str] = Field(default=None, description="Estimated salary or salary range")
    remote_policy: Optional[str] = Field(default=None, description="Remote work policy")
    benefits: List[str] = Field(default_factory=list, description="Extra benefits offered")
    company_description: Optional[str] = Field(default=None, description="Short description of the company")
    company_industry: Optional[str] = Field(default=None, description="Sector or industry")
    company_size: Optional[str] = Field(default=None, description="Company size")
    posted_date: Optional[str] = Field(default=None, description="Date of publication")
    days_ago: Optional[str] = Field(default=None, description="Relative publication age")
    application_deadline: Optional[str] = Field(default=None, description="Deadline to apply")
    application_method: Optional[str] = Field(default=None, description="How to apply")
    application_url: Optional[str] = Field(default=None, description="Direct application URL")
    application_email: Optional[str] = Field(default=None, description="Application email address")
    application_instructions: Optional[str] = Field(default=None, description="Short instructions on how to apply")
    reference_number: Optional[str] = Field(default=None, description="Internal reference code")
    contact_info: Optional[str] = Field(default=None, description="Email or contact person")
    original_language: Optional[str] = Field(default=None, description="Detected ISO 639-1 language code")


# ── Apply side ───────────────────────────────────────────────────────────────

class FormSelectors(BaseModel):
    """CSS selectors validated against the live DOM before interaction.

    Mandatory selectors: absence raises PortalStructureChangedError.
    Optional selectors: absence is logged as a warning and the interaction is skipped.
    """

    # Mandatory
    apply_button: str
    cv_upload: str
    submit_button: str
    success_indicator: str

    # Optional
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    letter_upload: str | None = None
    error_indicator: str | None = None
    cv_select_existing: str | None = None


class ApplicationRecord(BaseModel):
    """Persisted record of one apply attempt for a specific job."""

    source: str
    job_id: str
    job_title: str
    company_name: str
    application_url: str
    cv_path: str
    letter_path: str | None
    fields_filled: list[str]
    dry_run: bool
    submitted_at: str | None
    confirmation_text: str | None


class ApplyMeta(BaseModel):
    """Small status artifact describing the outcome of an apply run."""

    status: Literal["submitted", "dry_run", "failed", "portal_changed"]
    timestamp: str
    error: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_models.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/motors/crawl4ai/models.py tests/unit/automation/motors/crawl4ai/test_models.py
git commit -m "feat(crawl4ai): add merged C4AI models — JobPosting, FormSelectors, ApplicationRecord, ApplyMeta"
```

---

## Task 6: Move C4AI extraction schemas

**Files:**
- Create: `src/automation/motors/crawl4ai/schemas/stepstone_schema.json`
- Create: `src/automation/motors/crawl4ai/schemas/tuberlin_schema.json`
- Create: `src/automation/motors/crawl4ai/schemas/xing_schema.json`

- [ ] **Step 1: Copy JSON files to new location**

```bash
cp data/ariadne/assets/crawl4ai_schemas/stepstone_schema.json src/automation/motors/crawl4ai/schemas/
cp data/ariadne/assets/crawl4ai_schemas/tuberlin_schema.json  src/automation/motors/crawl4ai/schemas/
cp data/ariadne/assets/crawl4ai_schemas/xing_schema.json      src/automation/motors/crawl4ai/schemas/
```

- [ ] **Step 2: Verify files are present**

```bash
ls src/automation/motors/crawl4ai/schemas/
```

Expected: `stepstone_schema.json  tuberlin_schema.json  xing_schema.json`

- [ ] **Step 3: Commit**

```bash
git add src/automation/motors/crawl4ai/schemas/
git commit -m "chore(crawl4ai): move extraction schemas to motor-local schemas/"
```

---

## Task 7: Move C4AI scrape engine

Move `src/scraper/smart_adapter.py` → `src/automation/motors/crawl4ai/scrape_engine.py`. Update the two internal imports.

**Files:**
- Create: `src/automation/motors/crawl4ai/scrape_engine.py`
- Create: `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py`

- [ ] **Step 1: Write the failing test**

Copy `tests/unit/scraper/test_smart_adapter.py` to the new location and update the import:

```python
# tests/unit/automation/motors/crawl4ai/test_scrape_engine.py
# — identical to tests/unit/scraper/test_smart_adapter.py except:
#   CHANGE: from src.scraper.smart_adapter import SmartScraperAdapter
#   TO:     from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
```

Full file — copy entire content of `tests/unit/scraper/test_smart_adapter.py`, then change the one import line:

```python
from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_scrape_engine.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Copy scrape engine and update imports**

Copy `src/scraper/smart_adapter.py` to `src/automation/motors/crawl4ai/scrape_engine.py`, then change two lines:

```python
# CHANGE:
from src.scraper.models import JobPosting
# TO:
from src.automation.motors.crawl4ai.models import JobPosting
```

The `src.core.data_manager` and `src.shared.log_tags` imports stay unchanged.

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_scrape_engine.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/motors/crawl4ai/scrape_engine.py tests/unit/automation/motors/crawl4ai/test_scrape_engine.py
git commit -m "feat(crawl4ai): move scrape engine to motors/crawl4ai/scrape_engine"
```

---

## Task 8: Move C4AI apply engine

Move `src/apply/smart_adapter.py` → `src/automation/motors/crawl4ai/apply_engine.py`. Update one internal import.

**Files:**
- Create: `src/automation/motors/crawl4ai/apply_engine.py`
- Create: `tests/unit/automation/motors/crawl4ai/test_apply_engine.py`

- [ ] **Step 1: Write the failing test**

Copy `tests/unit/apply/test_smart_adapter.py` to new location and update imports:

```python
# tests/unit/automation/motors/crawl4ai/test_apply_engine.py
# Two import changes from the original test:
#   CHANGE: from src.apply.models import FormSelectors
#   TO:     from src.automation.motors.crawl4ai.models import FormSelectors
#
#   CHANGE: from src.apply.smart_adapter import ApplyAdapter, PortalStructureChangedError
#   TO:     from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter, PortalStructureChangedError
```

Copy the full content of `tests/unit/apply/test_smart_adapter.py` and apply those two import substitutions.

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_apply_engine.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Copy apply engine and update import**

Copy `src/apply/smart_adapter.py` to `src/automation/motors/crawl4ai/apply_engine.py`, then change one line:

```python
# CHANGE:
from src.apply.models import ApplicationRecord, ApplyMeta, FormSelectors
# TO:
from src.automation.motors.crawl4ai.models import ApplicationRecord, ApplyMeta, FormSelectors
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_apply_engine.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/motors/crawl4ai/apply_engine.py tests/unit/automation/motors/crawl4ai/test_apply_engine.py
git commit -m "feat(crawl4ai): move apply engine to motors/crawl4ai/apply_engine"
```

---

## Task 9: Rewrite C4AI scrape portal translators

Rewrite the three scrape adapters to consume portal intent. Each extends `SmartScraperAdapter`, imports its `ScrapePortalDefinition`, and derives `source_name`, `supported_params`, and `extract_job_id` from it. URL building and link extraction remain as methods.

**Files:**
- Create: `src/automation/motors/crawl4ai/portals/stepstone/scrape.py`
- Create: `src/automation/motors/crawl4ai/portals/xing/scrape.py`
- Create: `src/automation/motors/crawl4ai/portals/tuberlin/scrape.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/stepstone/test_scrape.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/xing/test_scrape.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/tuberlin/test_scrape.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/automation/motors/crawl4ai/portals/stepstone/test_scrape.py
from src.automation.motors.crawl4ai.portals.stepstone.scrape import StepStoneAdapter

def test_source_name():
    adapter = StepStoneAdapter()
    assert adapter.source_name == "stepstone"

def test_supported_params():
    adapter = StepStoneAdapter()
    assert "job_query" in adapter.supported_params
    assert "city" in adapter.supported_params
    assert "max_days" in adapter.supported_params

def test_extract_job_id():
    adapter = StepStoneAdapter()
    url = "https://www.stepstone.de/stellenangebote--data-engineer--12345678-inline.html"
    assert adapter.extract_job_id(url) == "12345678"

def test_extract_job_id_unknown():
    adapter = StepStoneAdapter()
    assert adapter.extract_job_id("https://www.stepstone.de/no-match") == "unknown"

def test_get_search_url_default():
    adapter = StepStoneAdapter()
    url = adapter.get_search_url(job_query="data scientist", city="berlin")
    assert "stepstone.de" in url
    assert "data-scientist" in url
    assert "berlin" in url
```

```python
# tests/unit/automation/motors/crawl4ai/portals/xing/test_scrape.py
from src.automation.motors.crawl4ai.portals.xing.scrape import XingAdapter

def test_source_name():
    assert XingAdapter().source_name == "xing"

def test_extract_job_id():
    adapter = XingAdapter()
    url = "https://www.xing.com/jobs/berlin-data-engineer-9876543"
    assert adapter.extract_job_id(url) == "9876543"
```

```python
# tests/unit/automation/motors/crawl4ai/portals/tuberlin/test_scrape.py
from src.automation.motors.crawl4ai.portals.tuberlin.scrape import TUBerlinAdapter

def test_source_name():
    assert TUBerlinAdapter().source_name == "tuberlin"

def test_supported_params():
    adapter = TUBerlinAdapter()
    assert "categories" in adapter.supported_params
    assert "job_query" in adapter.supported_params

def test_extract_job_id():
    adapter = TUBerlinAdapter()
    url = "https://www.jobs.tu-berlin.de/en/job-postings/11223344"
    assert adapter.extract_job_id(url) == "11223344"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/portals/ -v
```

Expected: `ImportError`

- [ ] **Step 3: Write the three scrape portal translators**

```python
# src/automation/motors/crawl4ai/portals/stepstone/scrape.py
"""StepStone C4AI scrape translator — consumes STEPSTONE_SCRAPE portal intent."""
from __future__ import annotations

import re
from typing import Any, List

from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
from src.automation.portals.stepstone.scrape import STEPSTONE_SCRAPE


class StepStoneAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for StepStone.de."""

    portal = STEPSTONE_SCRAPE

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    @property
    def supported_params(self) -> List[str]:
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
        query = (kwargs.get("job_query") or "data-scientist").replace(" ", "-")
        city = (kwargs.get("city") or "berlin").lower()
        max_days = kwargs.get("max_days")
        age_str = ""
        if max_days:
            if max_days <= 1:
                age_str = "age_1"
            elif max_days <= 7:
                age_str = "age_7"
            elif max_days <= 14:
                age_str = "age_14"
            else:
                age_str = "age_30"
        url = f"https://www.stepstone.de/jobs/{query}/in-{city}"
        if age_str:
            url += f"?ag={age_str}"
        return url

    def extract_links(self, crawl_result: Any) -> List[str]:
        job_links = []
        all_links = crawl_result.links.get("internal", []) + crawl_result.links.get("external", [])
        for link in all_links:
            href = link.get("href", "")
            if "-inline.html" in href and "stepstone.de" in href:
                job_links.append(href)
        return list(dict.fromkeys(job_links))

    def get_llm_instructions(self) -> str:
        return (
            "Extract from stepstone.de. Job title is in the <h1>. "
            "Salary often appears as a range. Remote policy may appear as 'Homeoffice'. "
            "Detect the primary language and return its ISO 639-1 code."
        )
```

```python
# src/automation/motors/crawl4ai/portals/xing/scrape.py
"""XING C4AI scrape translator — consumes XING_SCRAPE portal intent."""
from __future__ import annotations

import re
from typing import Any, List

from bs4 import BeautifulSoup

from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
from src.automation.portals.xing.scrape import XING_SCRAPE


class XingAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for XING."""

    portal = XING_SCRAPE

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    @property
    def supported_params(self) -> List[str]:
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
        query = (kwargs.get("job_query") or "data-scientist").replace(" ", "%20")
        city = (kwargs.get("city") or "berlin").replace(" ", "%20")
        max_days = kwargs.get("max_days")
        age_str = ""
        if max_days:
            if max_days <= 1:
                age_str = "1"
            elif max_days <= 7:
                age_str = "7"
            elif max_days <= 14:
                age_str = "14"
            else:
                age_str = "30"
        url = f"https://www.xing.com/jobs/search?keywords={query}&location={city}"
        if age_str:
            url += f"&date={age_str}"
        return url

    def extract_links(self, crawl_result: Any) -> List[dict[str, Any]]:
        html = crawl_result.cleaned_html or getattr(crawl_result, "html", "")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        job_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"-(\d+)$", href) and "xing.com/jobs/" in href:
                job_links.append({"href": href, "text": a.get_text(strip=True)})
        seen = set()
        unique = []
        for item in job_links:
            if item["href"] not in seen:
                seen.add(item["href"])
                unique.append(item)
        return unique

    def get_llm_instructions(self) -> str:
        return (
            "Extract from xing.com. Job title is in the <h1>. "
            "Salary and remote policy may appear in a facts sidebar. "
            "Detect the primary language and return its ISO 639-1 code."
        )
```

```python
# src/automation/motors/crawl4ai/portals/tuberlin/scrape.py
"""TU Berlin C4AI scrape translator — consumes TUBERLIN_SCRAPE portal intent."""
from __future__ import annotations

import re
from typing import Any, List

from src.automation.motors.crawl4ai.scrape_engine import SmartScraperAdapter
from src.automation.portals.tuberlin.scrape import TUBERLIN_SCRAPE


class TUBerlinAdapter(SmartScraperAdapter):
    """C4AI scrape adapter for TU Berlin (Stellenticket)."""

    portal = TUBERLIN_SCRAPE

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    @property
    def supported_params(self) -> List[str]:
        return self.portal.supported_params

    def extract_job_id(self, url: str) -> str:
        match = re.search(self.portal.job_id_pattern, url)
        return match.group(1) if match else "unknown"

    def get_search_url(self, **kwargs) -> str:
        categories = kwargs.get("categories")
        job_query = kwargs.get("job_query") or ""
        base = f"https://www.jobs.tu-berlin.de/en/job-postings?filter%5Bfulltextsearch%5D={job_query}"
        mapping = {
            "wiss-mlehr": "Research assistant with teaching obligation",
            "wiss-olehr": "Research assistant without teaching obligation",
            "besch-abgwiss": "Beschäftigte*r mit abgeschl. wiss. Hochschulbildung",
            "techn-besch": "Techn. Beschäftigte*r",
            "besch-itb": "Beschäftigte*r in der IT-Betreuung",
            "besch-itsys": "Beschäftigte*r in der IT-Systemtechnik",
            "besch-prog": "Beschäftigte*r in der Programmierung",
        }
        cat_list = [k for k in mapping if not categories or k in categories]
        filters = [f"filter%5Bworktype_tub%5D%5B%5D={cat}" for cat in cat_list]
        return f"{base}&{'&'.join(filters)}"

    def extract_links(self, crawl_result: Any) -> List[str]:
        job_links = []
        for link in crawl_result.links.get("internal", []):
            href = link.get("href", "")
            if "/job-postings/" in href and "apply" not in href and "download" not in href:
                if href.startswith("/"):
                    href = f"https://www.jobs.tu-berlin.de{href}"
                if href.startswith("https://"):
                    job_links.append(href)
        return sorted(set(job_links))

    def get_llm_instructions(self) -> str:
        return (
            "Extract from jobs.tu-berlin.de (Stellenticket). Pages can be German or English. "
            "Company is always Technische Universität Berlin or a specific faculty. "
            "Salary is usually a TV-L grade. Detect the primary language ISO 639-1 code."
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/portals/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/motors/crawl4ai/portals/ tests/unit/automation/motors/crawl4ai/portals/
git commit -m "feat(crawl4ai): add scrape portal translators — stepstone, xing, tuberlin"
```

---

## Task 10: Rewrite C4AI apply portal translators

Rewrite the three apply adapters to consume portal intent. `source_name` and `_get_portal_base_url` derive from the definition. CSS selectors and C4A-Scripts remain as methods.

**Files:**
- Create: `src/automation/motors/crawl4ai/portals/linkedin/apply.py`
- Create: `src/automation/motors/crawl4ai/portals/stepstone/apply.py`
- Create: `src/automation/motors/crawl4ai/portals/xing/apply.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/linkedin/test_apply.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/stepstone/test_apply.py`
- Create: `tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py`

- [ ] **Step 1: Write the failing tests**

Copy `tests/unit/apply/providers/linkedin/test_adapter.py` to `tests/unit/automation/motors/crawl4ai/portals/linkedin/test_apply.py` and update the adapter import:

```python
# Change:
from src.apply.providers.linkedin.adapter import LinkedInApplyAdapter
# To:
from src.automation.motors.crawl4ai.portals.linkedin.apply import LinkedInApplyAdapter
```

Do the same for stepstone and xing adapter tests.

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/portals/linkedin/ tests/unit/automation/motors/crawl4ai/portals/stepstone/ tests/unit/automation/motors/crawl4ai/portals/xing/ -v
```

Expected: `ImportError`

- [ ] **Step 3: Write the three apply portal translators**

```python
# src/automation/motors/crawl4ai/portals/linkedin/apply.py
"""LinkedIn C4AI apply translator — consumes LINKEDIN_APPLY portal intent."""
from __future__ import annotations

from pathlib import Path

from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter
from src.automation.motors.crawl4ai.models import FormSelectors
from src.automation.portals.linkedin.apply import LINKEDIN_APPLY


class LinkedInApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for LinkedIn Easy Apply."""

    portal = LINKEDIN_APPLY

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    def _get_portal_base_url(self) -> str:
        return self.portal.base_url

    def get_session_profile_dir(self) -> Path:
        return Path("data/profiles/linkedin_profile")

    def get_form_selectors(self) -> FormSelectors:
        return FormSelectors(
            apply_button="button.jobs-apply-button",
            cv_upload="input[type='file'][accept*='pdf']",
            submit_button="button.jp-apply-form-submit",
            success_indicator="[data-test-modal-id='post-apply-modal']",
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phoneNumber']",
            letter_upload=None,
            cv_select_existing="button.jobs-resume-picker__resume-list-item-select-btn",
        )

    def get_open_modal_script(self) -> str:
        return """
IF NOT `[data-test-modal-id="apply-modal"]` THEN
  CLICK `button.jobs-apply-button`
  WAIT `[data-test-modal-id="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        del profile
        return """
IF `input[name="firstName"]` THEN
  SET `input[name="firstName"]` "{{first_name}}"
END
IF `input[name="lastName"]` THEN
  SET `input[name="lastName"]` "{{last_name}}"
END
IF `input[type="email"]` THEN
  SET `input[type="email"]` "{{email}}"
END
IF `input[name="phoneNumber"]` THEN
  SET `input[name="phoneNumber"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        return """
CLICK `button.jp-apply-form-submit`
WAIT `[data-test-modal-id="post-apply-modal"]` 15
"""

    def get_success_text(self) -> str:
        return "application"
```

```python
# src/automation/motors/crawl4ai/portals/stepstone/apply.py
"""StepStone C4AI apply translator — consumes STEPSTONE_APPLY portal intent."""
from __future__ import annotations

from pathlib import Path

from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter
from src.automation.motors.crawl4ai.models import FormSelectors
from src.automation.portals.stepstone.apply import STEPSTONE_APPLY


class StepStoneApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for StepStone Easy Apply."""

    portal = STEPSTONE_APPLY

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    def _get_portal_base_url(self) -> str:
        return self.portal.base_url

    def get_session_profile_dir(self) -> Path:
        return Path("data/profiles/stepstone_profile")

    def get_form_selectors(self) -> FormSelectors:
        return FormSelectors(
            apply_button="[data-at='apply-button']",
            cv_upload="input[type='file']",
            submit_button="[data-at='submit-button']",
            success_indicator="[data-at='application-success']",
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,
            cv_select_existing=None,
        )

    def get_open_modal_script(self) -> str:
        return """
IF NOT `[data-at="apply-modal"]` THEN
  CLICK `[data-at="apply-button"]`
  WAIT `[data-at="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        del profile
        return """
SET `input[name="firstName"]` "{{first_name}}"
SET `input[name="lastName"]` "{{last_name}}"
SET `input[type="email"]` "{{email}}"
IF `input[name="phone"]` THEN
  SET `input[name="phone"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        return """
CLICK `[data-at="submit-button"]`
WAIT `[data-at="application-success"]` 15
"""

    def get_success_text(self) -> str:
        return "Bewerbung"
```

```python
# src/automation/motors/crawl4ai/portals/xing/apply.py
"""XING C4AI apply translator — consumes XING_APPLY portal intent."""
from __future__ import annotations

from pathlib import Path

from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter
from src.automation.motors.crawl4ai.models import FormSelectors
from src.automation.portals.xing.apply import XING_APPLY


class XingApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for XING Easy Apply."""

    portal = XING_APPLY

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    def _get_portal_base_url(self) -> str:
        return self.portal.base_url

    def get_session_profile_dir(self) -> Path:
        return Path("data/profiles/xing_profile")

    def get_form_selectors(self) -> FormSelectors:
        return FormSelectors(
            apply_button="[data-testid='apply-button']",
            cv_upload="input[type='file'][accept*='pdf']",
            submit_button="[data-testid='submit-button']",
            success_indicator="[data-testid='application-success']",
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,
            cv_select_existing=None,
        )

    def get_open_modal_script(self) -> str:
        return """
IF NOT `[data-testid="apply-modal"]` THEN
  CLICK `[data-testid="apply-button"]`
  WAIT `[data-testid="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        del profile
        return """
SET `input[name="firstName"]` "{{first_name}}"
SET `input[name="lastName"]` "{{last_name}}"
SET `input[type="email"]` "{{email}}"
IF `input[name="phone"]` THEN
  SET `input[name="phone"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        return """
CLICK `[data-testid="submit-button"]`
WAIT `[data-testid="application-success"]` 15
"""

    def get_success_text(self) -> str:
        return "Bewerbung"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/portals/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/motors/crawl4ai/portals/ tests/unit/automation/motors/crawl4ai/portals/
git commit -m "feat(crawl4ai): add apply portal translators — linkedin, stepstone, xing"
```

---

## Task 11: Move BrowserOS motor

Move all four BrowserOS files, update their internal imports, move the trace JSON, and migrate the three test files.

**Files:**
- Create: `src/automation/motors/browseros/cli/client.py`
- Create: `src/automation/motors/browseros/cli/executor.py`
- Create: `src/automation/motors/browseros/cli/backend.py`
- Create: `src/automation/motors/browseros/cli/models.py`
- Create: `src/automation/motors/browseros/cli/traces/linkedin_easy_apply_v1.json`
- Create: `tests/unit/automation/motors/browseros/cli/test_client.py`
- Create: `tests/unit/automation/motors/browseros/cli/test_executor.py`
- Create: `tests/unit/automation/motors/browseros/cli/test_models.py`

- [ ] **Step 1: Write the failing tests**

Copy each BrowserOS test file and update the one import in each:

`tests/unit/automation/motors/browseros/cli/test_client.py`:
```python
# Change:
from src.apply.browseros_client import BrowserOSClient
# To:
from src.automation.motors.browseros.cli.client import BrowserOSClient
```

`tests/unit/automation/motors/browseros/cli/test_models.py`:
```python
# Change:
from src.apply.browseros_models import BrowserOSPlaybook
# To:
from src.automation.motors.browseros.cli.models import BrowserOSPlaybook
```
Also update the playbook path inside the test:
```python
# Change:
playbook_path = Path("src/apply/playbooks/linkedin_easy_apply_v1.json")
# To:
playbook_path = Path("src/automation/motors/browseros/cli/traces/linkedin_easy_apply_v1.json")
```

`tests/unit/automation/motors/browseros/cli/test_executor.py`:
```python
# Change:
from src.apply.browseros_client import BrowserOSClient, SnapshotElement
from src.apply.browseros_executor import BrowserOSObserveError, BrowserOSPlaybookExecutor
from src.apply.browseros_models import BrowserOSPlaybook, ObserveBlock, PlaybookAction, PlaybookStep
# To:
from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement
from src.automation.motors.browseros.cli.executor import BrowserOSObserveError, BrowserOSPlaybookExecutor
from src.automation.motors.browseros.cli.models import BrowserOSPlaybook, ObserveBlock, PlaybookAction, PlaybookStep
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/automation/motors/browseros/cli/ -v
```

Expected: `ImportError`

- [ ] **Step 3: Copy BrowserOS files and update imports**

```bash
cp src/apply/browseros_models.py   src/automation/motors/browseros/cli/models.py
cp src/apply/browseros_client.py   src/automation/motors/browseros/cli/client.py
cp src/apply/browseros_executor.py src/automation/motors/browseros/cli/executor.py
cp src/apply/browseros_backend.py  src/automation/motors/browseros/cli/backend.py
cp src/apply/playbooks/linkedin_easy_apply_v1.json \
   src/automation/motors/browseros/cli/traces/linkedin_easy_apply_v1.json
```

Update imports in `executor.py` (two lines):
```python
# Change:
from src.apply.browseros_client import BrowserOSClient, SnapshotElement
from src.apply.browseros_models import BrowserOSPlaybook, ExpectedElement, PlaybookAction
# To:
from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement
from src.automation.motors.browseros.cli.models import BrowserOSPlaybook, ExpectedElement, PlaybookAction
```

Update imports in `backend.py` (four lines):
```python
# Change:
from src.apply.browseros_client import BrowserOSClient
from src.apply.browseros_executor import BrowserOSObserveError, BrowserOSPlaybookExecutor
from src.apply.browseros_models import BrowserOSPlaybook
from src.apply.models import ApplicationRecord, ApplyMeta
# To:
from src.automation.motors.browseros.cli.client import BrowserOSClient
from src.automation.motors.browseros.cli.executor import BrowserOSObserveError, BrowserOSPlaybookExecutor
from src.automation.motors.browseros.cli.models import BrowserOSPlaybook
from src.automation.motors.crawl4ai.models import ApplicationRecord, ApplyMeta
```

Also update the playbook path in `backend.py`:
```python
# Change:
playbook_dir = Path(__file__).resolve().parent / "playbooks"
# To:
playbook_dir = Path(__file__).resolve().parent / "traces"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/motors/browseros/cli/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/motors/browseros/ tests/unit/automation/motors/browseros/
git commit -m "feat(browseros): move BrowserOS CLI motor to motors/browseros/cli/"
```

---

## Task 12: Create unified CLI

Merge `src/scraper/main.py` and `src/apply/main.py` into `src/automation/main.py` with `scrape` and `apply` subcommands.

**Files:**
- Create: `src/automation/main.py`
- Create: `tests/unit/automation/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/test_cli.py
"""Tests for the unified automation CLI parser."""
from __future__ import annotations

import pytest

from src.automation.main import build_parser


def test_scrape_subcommand_requires_source():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape"])


def test_scrape_parses_source_and_defaults():
    parser = build_parser()
    args = parser.parse_args(["scrape", "--source", "stepstone"])
    assert args.command == "scrape"
    assert args.source == "stepstone"
    assert args.overwrite is False
    assert args.limit is None


def test_scrape_parses_all_options():
    parser = build_parser()
    args = parser.parse_args([
        "scrape", "--source", "xing",
        "--job-query", "data scientist",
        "--city", "berlin",
        "--max-days", "7",
        "--limit", "10",
        "--overwrite",
    ])
    assert args.job_query == "data scientist"
    assert args.max_days == 7
    assert args.limit == 10
    assert args.overwrite is True


def test_apply_subcommand_requires_source():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["apply"])


def test_apply_parses_apply_mode():
    parser = build_parser()
    args = parser.parse_args([
        "apply", "--source", "xing",
        "--job-id", "12345",
        "--cv", "/path/cv.pdf",
        "--dry-run",
    ])
    assert args.command == "apply"
    assert args.source == "xing"
    assert args.job_id == "12345"
    assert args.cv_path == "/path/cv.pdf"
    assert args.dry_run is True
    assert args.backend == "crawl4ai"


def test_apply_parses_setup_session():
    parser = build_parser()
    args = parser.parse_args(["apply", "--source", "xing", "--setup-session"])
    assert args.setup_session is True
    assert args.job_id is None


def test_apply_parses_browseros_backend():
    parser = build_parser()
    args = parser.parse_args([
        "apply", "--backend", "browseros",
        "--source", "linkedin",
        "--job-id", "99",
        "--cv", "/cv.pdf",
    ])
    assert args.backend == "browseros"
    assert args.source == "linkedin"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/automation/test_cli.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write the unified CLI**

```python
# src/automation/main.py
"""Unified automation CLI.

Subcommands:
  scrape  — job discovery and ingestion
  apply   — job auto-application
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
from pathlib import Path


def _setup_logging(label: str) -> None:
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(f"logs/{label}_{timestamp}.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def _add_scrape_subcommand(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("scrape", help="Job discovery and ingestion")
    p.add_argument("--source", required=True, choices=["tuberlin", "stepstone", "xing"])
    p.add_argument("--drop-repeated", dest="drop_repeated", action="store_true", default=True)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--categories", nargs="+")
    p.add_argument("--city")
    p.add_argument("--job-query", dest="job_query")
    p.add_argument("--max-days", dest="max_days", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--save-html", action="store_true")


def _add_apply_subcommand(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("apply", help="Job auto-application")
    p.add_argument("--backend", choices=["crawl4ai", "browseros"], default="crawl4ai")
    p.add_argument("--source", required=True, choices=["xing", "stepstone", "linkedin"])
    p.add_argument("--job-id", dest="job_id")
    p.add_argument("--cv", dest="cv_path")
    p.add_argument("--letter", dest="letter_path")
    p.add_argument("--profile-json", dest="profile_json")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    p.add_argument("--setup-session", dest="setup_session", action="store_true", default=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automation CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_scrape_subcommand(sub)
    _add_apply_subcommand(sub)
    return parser


async def _run_scrape(args) -> None:
    from src.automation.motors.crawl4ai.portals.stepstone.scrape import StepStoneAdapter
    from src.automation.motors.crawl4ai.portals.tuberlin.scrape import TUBerlinAdapter
    from src.automation.motors.crawl4ai.portals.xing.scrape import XingAdapter
    from src.core.data_manager import DataManager
    from src.shared.log_tags import LogTag

    _setup_logging(f"scrape_{args.source}")
    logger = logging.getLogger(__name__)
    data_manager = DataManager()
    providers = {
        "tuberlin": TUBerlinAdapter(data_manager),
        "stepstone": StepStoneAdapter(data_manager),
        "xing": XingAdapter(data_manager),
    }
    adapter = providers[args.source]
    for param, value in {"categories": args.categories, "city": args.city, "job_query": args.job_query, "max_days": args.max_days}.items():
        if value is not None and param not in adapter.supported_params:
            logger.warning("%s Provider '%s' does not support '%s'; ignoring.", LogTag.WARN, args.source, param)
    already_scraped: list[str] = []
    if not args.overwrite:
        source_root = data_manager.source_root(args.source)
        if source_root.exists():
            already_scraped = sorted(p.name for p in source_root.iterdir() if p.is_dir() and data_manager.has_ingested_job(args.source, p.name))
    ingested = await adapter.run(already_scraped=already_scraped, **vars(args))
    logger.info("%s Ingested %s jobs for source '%s'", LogTag.OK, len(ingested), args.source)


async def _run_apply(args) -> None:
    from src.shared.log_tags import LogTag

    _setup_logging(f"apply_{args.source}")
    logger = logging.getLogger(__name__)
    profile_data = None
    if args.profile_json:
        profile_data = json.loads(Path(args.profile_json).read_text(encoding="utf-8"))
    if args.backend == "browseros":
        from src.automation.motors.browseros.cli.backend import build_browseros_providers
        from src.core.data_manager import DataManager
        providers = build_browseros_providers(DataManager(), profile_data=profile_data)
    else:
        from src.automation.motors.crawl4ai.portals.linkedin.apply import LinkedInApplyAdapter
        from src.automation.motors.crawl4ai.portals.stepstone.apply import StepStoneApplyAdapter
        from src.automation.motors.crawl4ai.portals.xing.apply import XingApplyAdapter
        from src.core.data_manager import DataManager
        manager = DataManager()
        providers = {
            "linkedin": LinkedInApplyAdapter(manager),
            "xing": XingApplyAdapter(manager),
            "stepstone": StepStoneApplyAdapter(manager),
        }
    if args.source not in providers:
        logger.error("%s Backend '%s' does not support source '%s'.", LogTag.FAIL, args.backend, args.source)
        sys.exit(1)
    if args.setup_session and args.job_id:
        logger.error("%s --setup-session and --job-id are mutually exclusive.", LogTag.FAIL)
        sys.exit(1)
    if args.setup_session:
        await providers[args.source].setup_session()
        return
    if not args.job_id or not args.cv_path:
        logger.error("%s --job-id and --cv are required in apply mode.", LogTag.FAIL)
        sys.exit(1)
    meta = await providers[args.source].run(
        job_id=args.job_id,
        cv_path=Path(args.cv_path),
        letter_path=Path(args.letter_path) if args.letter_path else None,
        dry_run=args.dry_run,
    )
    logger.info("%s Apply completed: status=%s", LogTag.OK, meta.status)


async def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv or sys.argv[1:])
    if args.command == "scrape":
        await _run_scrape(args)
    elif args.command == "apply":
        await _run_apply(args)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/automation/test_cli.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/automation/main.py tests/unit/automation/test_cli.py
git commit -m "feat(automation): add unified CLI with scrape and apply subcommands"
```

---

## Task 13: Run full new test suite, delete old packages, update sparse checkout

- [ ] **Step 1: Run all new automation tests**

```bash
python -m pytest tests/unit/automation/ -v
```

Expected: all PASS. Fix any import failures before continuing.

- [ ] **Step 2: Remove old source packages**

```bash
git rm -r src/scraper/ src/apply/
```

Expected: many `rm` lines, no errors.

- [ ] **Step 3: Remove old test directories**

```bash
git rm -r tests/unit/scraper/ tests/unit/apply/
```

- [ ] **Step 4: Update sparse checkout — remove old paths, keep new**

```bash
git sparse-checkout set \
  data \
  docs/standards \
  docs/superpowers \
  plan_docs/automation \
  plan_docs/ariadne \
  plan_docs/contracts \
  plan_docs/motors \
  plan_docs/planning \
  src/automation \
  src/core \
  src/shared \
  tests/unit/automation
```

- [ ] **Step 5: Run full test suite to confirm nothing is broken**

```bash
python -m pytest tests/unit/automation/ -q
```

Expected: all PASS, 0 errors.

- [ ] **Step 6: Commit**

```bash
git add -u
git commit -m "refactor: complete migration to src/automation — remove src/scraper and src/apply"
```

---

## Self-review

**Spec coverage:**
- Ariadne portal schema (`portal_models.py`) — Task 2 ✓
- Portal intent files for scraping — Task 3 ✓
- Portal intent files for applying — Task 4 ✓
- C4AI models merged — Task 5 ✓
- C4AI schemas moved — Task 6 ✓
- C4AI scrape engine moved — Task 7 ✓
- C4AI apply engine moved — Task 8 ✓
- C4AI scrape portal translators consuming portal intent — Task 9 ✓
- C4AI apply portal translators consuming portal intent — Task 10 ✓
- BrowserOS motor moved — Task 11 ✓
- Unified CLI — Task 12 ✓
- Old packages deleted — Task 13 ✓

**Type consistency check:**
- `SmartScraperAdapter` used consistently in Tasks 7 and 9 ✓
- `ApplyAdapter` used consistently in Tasks 8 and 10 ✓
- `FormSelectors`, `ApplyMeta`, `ApplicationRecord` defined in Task 5, consumed in Tasks 10 and 11 ✓
- `BrowserOSPlaybook` defined (moved) in Task 11, trace path updated ✓
- `build_parser` defined in Task 12, tested in same task ✓
- `STEPSTONE_SCRAPE`, `XING_SCRAPE`, `TUBERLIN_SCRAPE` defined in Task 3, consumed in Task 9 ✓
- `LINKEDIN_APPLY`, `STEPSTONE_APPLY`, `XING_APPLY` defined in Task 4, consumed in Task 10 ✓
