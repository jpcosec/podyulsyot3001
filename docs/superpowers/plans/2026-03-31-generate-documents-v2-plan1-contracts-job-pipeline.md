# Generate Documents V2 — Plan 1: Contracts, Storage & Job Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full contract layer, artifact storage, profile loader, and the two job-parsing nodes (Ingestion J1→J2 and Requirement Filter J2→J3) for the new generate-documents pipeline.

**Architecture:** New module `src/core/ai/generate_documents_v2/` isolated from the current `generate_documents/` so nothing breaks. Contracts split by responsibility into focused files. Nodes are pure functions with injected LLM chains so tests never need real API keys. Storage follows the same `DataManager`-based pattern as `MatchArtifactStore`.

**Tech Stack:** Python 3.13, Pydantic v2, LangChain + `ChatGoogleGenerativeAI`, pytest with `tmp_path`.

---

## File Map

### Create (new module)

| File | Responsibility |
|------|---------------|
| `src/core/ai/generate_documents_v2/__init__.py` | Public re-exports |
| `src/core/ai/generate_documents_v2/contracts/__init__.py` | Re-exports all contracts |
| `src/core/ai/generate_documents_v2/contracts/base.py` | `TextAnchor`, `IdeaFact` |
| `src/core/ai/generate_documents_v2/contracts/profile.py` | `ProfileEntry`, `EvidenceEdge`, `ProfileKG`, `SectionMappingItem` |
| `src/core/ai/generate_documents_v2/contracts/job.py` | `JobRequirement`, `JobLogistics`, `CompanyData`, `JobKG`, `JobDelta` |
| `src/core/ai/generate_documents_v2/contracts/matching.py` | `MatchEdge` |
| `src/core/ai/generate_documents_v2/contracts/blueprint.py` | `SectionBlueprint`, `GlobalBlueprint` |
| `src/core/ai/generate_documents_v2/contracts/drafting.py` | `DraftedSection`, `DraftedDocument` |
| `src/core/ai/generate_documents_v2/contracts/assembly.py` | `MarkdownDocument`, `FinalMarkdownBundle` |
| `src/core/ai/generate_documents_v2/contracts/hitl.py` | `GraphPatch` |
| `src/core/ai/generate_documents_v2/storage.py` | `PipelineArtifactStore` |
| `src/core/ai/generate_documents_v2/profile_loader.py` | `load_profile_kg`, `load_section_mapping` |
| `src/core/ai/generate_documents_v2/nodes/__init__.py` | Empty |
| `src/core/ai/generate_documents_v2/nodes/ingestion.py` | Ingestion node + chain factory (J1→J2) |
| `src/core/ai/generate_documents_v2/nodes/requirement_filter.py` | Requirement Filter node + chain factory (J2→J3) |
| `src/core/ai/generate_documents_v2/prompts/__init__.py` | Empty |
| `src/core/ai/generate_documents_v2/prompts/ingestion.py` | System + user prompt builders for ingestion |
| `src/core/ai/generate_documents_v2/prompts/requirement_filter.py` | System + user prompt builders for requirement filter |

### Create (tests)

| File | Responsibility |
|------|---------------|
| `tests/test_generate_documents_v2/__init__.py` | Empty |
| `tests/test_generate_documents_v2/test_contracts.py` | Validation rules for all contracts |
| `tests/test_generate_documents_v2/test_profile_loader.py` | Load ProfileKG + SectionMapping from disk |
| `tests/test_generate_documents_v2/test_ingestion.py` | Ingestion node with fake chain |
| `tests/test_generate_documents_v2/test_requirement_filter.py` | Requirement Filter node with fake chain |

### Create (fixtures)

| File | Responsibility |
|------|---------------|
| `data/reference_data/profile/section_mapping.json` | Canonical section mapping for tests |

### Do NOT touch

- `src/core/ai/match_skill/` — stays unchanged
- `src/core/ai/generate_documents/` — stays unchanged (Plan 3 will cut over)
- `src/graph/` — stays unchanged until Plan 3

---

## Task 1: Base Contracts (`TextAnchor`, `IdeaFact`)

**Files:**
- Create: `src/core/ai/generate_documents_v2/contracts/base.py`
- Create: `tests/test_generate_documents_v2/test_contracts.py`

- [ ] **Step 1: Create the test file with tests for base contracts**

```python
# tests/test_generate_documents_v2/test_contracts.py
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.core.ai.generate_documents_v2.contracts.base import IdeaFact, TextAnchor


class TestTextAnchor:
    def test_valid_anchor(self):
        anchor = TextAnchor(
            document_id="job-001",
            start_index=10,
            end_index=50,
            exact_quote="Python experience required",
        )
        assert anchor.document_id == "job-001"
        assert anchor.exact_quote == "Python experience required"

    def test_rejects_negative_start(self):
        with pytest.raises(ValidationError):
            TextAnchor(
                document_id="d",
                start_index=-1,
                end_index=10,
                exact_quote="x",
            )

    def test_rejects_end_before_start(self):
        with pytest.raises(ValidationError):
            TextAnchor(
                document_id="d",
                start_index=20,
                end_index=5,
                exact_quote="x",
            )


class TestIdeaFact:
    def test_valid_fact(self):
        fact = IdeaFact(
            id="FACT001",
            provenance_refs=["EXP001"],
            core_content="Built Rust optimization engine",
            priority=3,
        )
        assert fact.status == "keep"
        assert fact.source_anchors == []

    def test_priority_out_of_range(self):
        with pytest.raises(ValidationError):
            IdeaFact(
                id="F1",
                provenance_refs=[],
                core_content="x",
                priority=6,
            )

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            IdeaFact(
                id="F1",
                provenance_refs=[],
                core_content="x",
                priority=3,
                status="unknown",
            )

    def test_empty_provenance_allowed(self):
        fact = IdeaFact(
            id="F1",
            provenance_refs=[],
            core_content="emergent evidence",
            priority=2,
        )
        assert fact.provenance_refs == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_contracts.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError` for `generate_documents_v2`

- [ ] **Step 3: Create the package skeleton and base contracts**

```python
# src/core/ai/generate_documents_v2/__init__.py
```

```python
# src/core/ai/generate_documents_v2/contracts/__init__.py
from src.core.ai.generate_documents_v2.contracts.base import IdeaFact, TextAnchor
from src.core.ai.generate_documents_v2.contracts.profile import (
    EvidenceEdge,
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)
from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.blueprint import (
    GlobalBlueprint,
    SectionBlueprint,
)
from src.core.ai.generate_documents_v2.contracts.drafting import (
    DraftedDocument,
    DraftedSection,
)
from src.core.ai.generate_documents_v2.contracts.assembly import (
    FinalMarkdownBundle,
    MarkdownDocument,
)
from src.core.ai.generate_documents_v2.contracts.hitl import GraphPatch

__all__ = [
    "TextAnchor",
    "IdeaFact",
    "ProfileEntry",
    "EvidenceEdge",
    "ProfileKG",
    "SectionMappingItem",
    "JobRequirement",
    "JobLogistics",
    "CompanyData",
    "JobKG",
    "JobDelta",
    "MatchEdge",
    "SectionBlueprint",
    "GlobalBlueprint",
    "DraftedSection",
    "DraftedDocument",
    "MarkdownDocument",
    "FinalMarkdownBundle",
    "GraphPatch",
]
```

```python
# src/core/ai/generate_documents_v2/contracts/base.py
"""Foundational traceability contracts shared across all pipeline stages."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TextAnchor(BaseModel):
    """Locates an exact quote within a source document for audit trails."""

    document_id: str
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    exact_quote: str

    @model_validator(mode="after")
    def _end_after_start(self) -> "TextAnchor":
        if self.end_index < self.start_index:
            raise ValueError("end_index must be >= start_index")
        return self


class IdeaFact(BaseModel):
    """Minimum traceable unit of information that can enter the pipeline."""

    id: str
    provenance_refs: list[str]
    core_content: str
    priority: int = Field(ge=1, le=5)
    status: Literal["keep", "hide", "merge"] = "keep"
    source_anchors: list[TextAnchor] = Field(default_factory=list)
```

- [ ] **Step 4: Create the remaining empty contract stubs so the `__init__` import resolves**

Create each file with just the class header — full content comes in Tasks 2-6.

```python
# src/core/ai/generate_documents_v2/contracts/profile.py
from __future__ import annotations
from pydantic import BaseModel, Field

class ProfileEntry(BaseModel):
    id: str
    role: str = ""
    organization: str = ""
    achievements: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None

class EvidenceEdge(BaseModel):
    from_id: str
    to_id: str
    relation: str

class ProfileKG(BaseModel):
    entries: list[ProfileEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    evidence_edges: list[EvidenceEdge] = Field(default_factory=list)

class SectionMappingItem(BaseModel):
    section_id: str
    target_document: str
    country_context: str = "global"
    mandatory: bool = True
    default_priority: int = Field(ge=1, le=5, default=3)
    style_guideline: str = ""
    default_fact_ids: list[str] = Field(default_factory=list)
    target_tone: str | None = None
```

```python
# src/core/ai/generate_documents_v2/contracts/job.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from src.core.ai.generate_documents_v2.contracts.base import TextAnchor

class JobRequirement(BaseModel):
    id: str
    text: str
    category: Literal["hard", "soft"] = "hard"
    priority: int = Field(ge=1, le=5, default=3)

class JobLogistics(BaseModel):
    location: str | None = None
    remote: bool | None = None
    contract_type: str | None = None
    relocation: bool | None = None
    visa_sponsorship: bool | None = None

class CompanyData(BaseModel):
    name: str | None = None
    contact_person: str | None = None
    department: str | None = None

class JobKG(BaseModel):
    hard_requirements: list[JobRequirement] = Field(default_factory=list)
    soft_context: list[JobRequirement] = Field(default_factory=list)
    logistics: JobLogistics = Field(default_factory=JobLogistics)
    company: CompanyData = Field(default_factory=CompanyData)
    source_anchors: list[TextAnchor] = Field(default_factory=list)

class JobDelta(BaseModel):
    must_highlight_skills: list[str] = Field(default_factory=list)
    ignored_requirements: list[str] = Field(default_factory=list)
    custom_instructions: str = ""
    soft_vibe_requirements: list[str] = Field(default_factory=list)
    logistics_flags: dict[str, bool] = Field(default_factory=dict)
```

```python
# src/core/ai/generate_documents_v2/contracts/matching.py
from __future__ import annotations
from pydantic import BaseModel, Field

class MatchEdge(BaseModel):
    requirement_id: str
    profile_evidence_ids: list[str] = Field(default_factory=list)
    match_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
```

```python
# src/core/ai/generate_documents_v2/contracts/blueprint.py
from __future__ import annotations
from pydantic import BaseModel, Field

class SectionBlueprint(BaseModel):
    section_id: str
    logical_train_of_thought: list[str]
    section_intent: str
    target_style: str | None = None
    word_count_target: int | None = None

class GlobalBlueprint(BaseModel):
    application_id: str
    strategy_type: str
    sections: list[SectionBlueprint] = Field(default_factory=list)
```

```python
# src/core/ai/generate_documents_v2/contracts/drafting.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class DraftedSection(BaseModel):
    section_id: str
    raw_markdown: str
    is_cohesive: bool = True
    word_count: int = 0

    @model_validator(mode="after")
    def _compute_word_count(self) -> "DraftedSection":
        if self.word_count == 0 and self.raw_markdown:
            self.word_count = len(self.raw_markdown.split())
        return self

class DraftedDocument(BaseModel):
    doc_type: Literal["cv", "letter", "email"]
    sections_md: dict[str, str] = Field(default_factory=dict)
    cohesion_score: float = Field(ge=0.0, le=1.0, default=1.0)
```

```python
# src/core/ai/generate_documents_v2/contracts/assembly.py
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

class MarkdownDocument(BaseModel):
    doc_type: Literal["cv", "letter", "email"]
    header_data: dict[str, Any] = Field(default_factory=dict)
    body_markdown: str
    footer_data: dict[str, Any] = Field(default_factory=dict)

class FinalMarkdownBundle(BaseModel):
    cv_full_md: str
    letter_full_md: str
    email_body_md: str
    rendering_metadata: dict[str, Any] = Field(default_factory=dict)
```

```python
# src/core/ai/generate_documents_v2/contracts/hitl.py
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel

PatchAction = Literal[
    "approve", "reject", "modify", "request_regeneration", "move_to_doc"
]

class GraphPatch(BaseModel):
    action: PatchAction
    target_id: str
    new_value: Any | None = None
    feedback_note: str = ""
    persist_to_profile: bool = False
    target_stage: str | None = None
    target_type: str | None = None
```

```python
# src/core/ai/generate_documents_v2/nodes/__init__.py
```

```python
# src/core/ai/generate_documents_v2/prompts/__init__.py
```

- [ ] **Step 5: Run base contract tests to verify they pass**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_contracts.py::TestTextAnchor tests/test_generate_documents_v2/test_contracts.py::TestIdeaFact -v
```

Expected: 7 tests pass

- [ ] **Step 6: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/ tests/test_generate_documents_v2/
git commit -m "feat: scaffold generate_documents_v2 — base contracts TextAnchor and IdeaFact"
```

---

## Task 2: Job Contracts (`JobKG`, `JobDelta`) — Full Validation

**Files:**
- Modify: `src/core/ai/generate_documents_v2/contracts/job.py` (add validators)
- Modify: `tests/test_generate_documents_v2/test_contracts.py` (add job contract tests)

- [ ] **Step 1: Add job contract tests**

Add to `tests/test_generate_documents_v2/test_contracts.py`:

```python
from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)


class TestJobRequirement:
    def test_defaults_to_hard(self):
        req = JobRequirement(id="R1", text="Python 3.10+")
        assert req.category == "hard"
        assert req.priority == 3

    def test_soft_category(self):
        req = JobRequirement(id="R2", text="Team player", category="soft", priority=2)
        assert req.category == "soft"

    def test_priority_out_of_range(self):
        with pytest.raises(ValidationError):
            JobRequirement(id="R3", text="x", priority=0)


class TestJobKG:
    def test_empty_defaults(self):
        kg = JobKG()
        assert kg.hard_requirements == []
        assert kg.soft_context == []
        assert kg.logistics.location is None
        assert kg.company.name is None

    def test_with_requirements(self):
        kg = JobKG(
            hard_requirements=[JobRequirement(id="R1", text="Rust")],
            soft_context=[JobRequirement(id="S1", text="Team culture", category="soft")],
            logistics=JobLogistics(location="Munich", relocation=True),
            company=CompanyData(name="Deutsche Bahn"),
        )
        assert len(kg.hard_requirements) == 1
        assert kg.logistics.relocation is True
        assert kg.company.name == "Deutsche Bahn"


class TestJobDelta:
    def test_empty_defaults(self):
        delta = JobDelta()
        assert delta.must_highlight_skills == []
        assert delta.custom_instructions == ""

    def test_with_highlights(self):
        delta = JobDelta(
            must_highlight_skills=["Rust", "Kafka"],
            ignored_requirements=["Nice to have: Haskell"],
            logistics_flags={"relocation_relevant": True},
        )
        assert "Rust" in delta.must_highlight_skills
        assert delta.logistics_flags["relocation_relevant"] is True
```

- [ ] **Step 2: Run new tests to verify they fail (import error only)**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_contracts.py::TestJobKG -v 2>&1 | head -15
```

Expected: PASS (stubs already exist from Task 1). If any fail, the stub is wrong — fix it.

- [ ] **Step 3: Rewrite `contracts/job.py` with full content (validators included)**

```python
# src/core/ai/generate_documents_v2/contracts/job.py
"""Job-side contracts: raw structured job knowledge graph and requirement delta."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.core.ai.generate_documents_v2.contracts.base import TextAnchor


class JobRequirement(BaseModel):
    """One requirement extracted from a job posting."""

    id: str
    text: str
    category: Literal["hard", "soft"] = "hard"
    priority: int = Field(ge=1, le=5, default=3)

    @field_validator("id", "text")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must be non-empty")
        return value.strip()


class JobLogistics(BaseModel):
    """Non-technical job context: location, contract, relocation."""

    location: str | None = None
    remote: bool | None = None
    contract_type: str | None = None
    relocation: bool | None = None
    visa_sponsorship: bool | None = None


class CompanyData(BaseModel):
    """Company-side metadata for assembly (headers, address blocks)."""

    name: str | None = None
    contact_person: str | None = None
    department: str | None = None


class JobKG(BaseModel):
    """Structured knowledge graph extracted from a raw job posting (J2)."""

    hard_requirements: list[JobRequirement] = Field(default_factory=list)
    soft_context: list[JobRequirement] = Field(default_factory=list)
    logistics: JobLogistics = Field(default_factory=JobLogistics)
    company: CompanyData = Field(default_factory=CompanyData)
    source_anchors: list[TextAnchor] = Field(default_factory=list)


class JobDelta(BaseModel):
    """Relevance filter: what to emphasize, what to ignore in this application (J3)."""

    must_highlight_skills: list[str] = Field(default_factory=list)
    ignored_requirements: list[str] = Field(default_factory=list)
    custom_instructions: str = ""
    soft_vibe_requirements: list[str] = Field(default_factory=list)
    logistics_flags: dict[str, bool] = Field(default_factory=dict)
```

- [ ] **Step 4: Run all contract tests so far**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_contracts.py -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/contracts/job.py tests/test_generate_documents_v2/test_contracts.py
git commit -m "feat: job contracts JobKG and JobDelta with validators"
```

---

## Task 3: Remaining Contracts (Profile, Blueprint, Drafting, Assembly, HITL)

**Files:**
- Modify: `src/core/ai/generate_documents_v2/contracts/profile.py`
- Modify: `src/core/ai/generate_documents_v2/contracts/blueprint.py`
- Modify: `src/core/ai/generate_documents_v2/contracts/drafting.py`
- Modify: `src/core/ai/generate_documents_v2/contracts/assembly.py`
- Modify: `src/core/ai/generate_documents_v2/contracts/hitl.py`
- Modify: `tests/test_generate_documents_v2/test_contracts.py`

- [ ] **Step 1: Add contract tests for remaining models**

Append to `tests/test_generate_documents_v2/test_contracts.py`:

```python
from src.core.ai.generate_documents_v2.contracts.profile import (
    EvidenceEdge,
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)
from src.core.ai.generate_documents_v2.contracts.blueprint import (
    GlobalBlueprint,
    SectionBlueprint,
)
from src.core.ai.generate_documents_v2.contracts.drafting import (
    DraftedDocument,
    DraftedSection,
)
from src.core.ai.generate_documents_v2.contracts.assembly import (
    FinalMarkdownBundle,
    MarkdownDocument,
)
from src.core.ai.generate_documents_v2.contracts.hitl import GraphPatch


class TestProfileKG:
    def test_empty_profile_kg(self):
        kg = ProfileKG()
        assert kg.entries == []
        assert kg.skills == []

    def test_with_entries(self):
        kg = ProfileKG(
            entries=[ProfileEntry(id="EXP001", role="Data Engineer", organization="ACME")],
            skills=["Python", "Rust"],
            traits=["curious", "railway-enthusiast"],
        )
        assert kg.entries[0].id == "EXP001"
        assert "Python" in kg.skills


class TestSectionMappingItem:
    def test_defaults(self):
        item = SectionMappingItem(section_id="summary", target_document="cv")
        assert item.mandatory is True
        assert item.country_context == "global"
        assert item.default_priority == 3

    def test_priority_validation(self):
        with pytest.raises(ValidationError):
            SectionMappingItem(section_id="x", target_document="cv", default_priority=0)


class TestSectionBlueprint:
    def test_valid(self):
        bp = SectionBlueprint(
            section_id="summary",
            logical_train_of_thought=["FACT001", "FACT002"],
            section_intent="Introduce technical background",
        )
        assert bp.word_count_target is None


class TestGlobalBlueprint:
    def test_valid(self):
        gb = GlobalBlueprint(
            application_id="APP001",
            strategy_type="Professional_German",
            sections=[
                SectionBlueprint(
                    section_id="summary",
                    logical_train_of_thought=["FACT001"],
                    section_intent="Lead with Rust experience",
                )
            ],
        )
        assert len(gb.sections) == 1


class TestDraftedSection:
    def test_word_count_computed(self):
        section = DraftedSection(
            section_id="summary",
            raw_markdown="I am a data engineer with experience in Rust.",
        )
        assert section.word_count == 9

    def test_explicit_word_count_respected(self):
        section = DraftedSection(
            section_id="summary",
            raw_markdown="short",
            word_count=99,
        )
        assert section.word_count == 99


class TestFinalMarkdownBundle:
    def test_canonical_fields(self):
        bundle = FinalMarkdownBundle(
            cv_full_md="# CV\n...",
            letter_full_md="# Letter\n...",
            email_body_md="Dear Hiring Team...",
        )
        assert bundle.rendering_metadata == {}


class TestGraphPatch:
    def test_approve_patch(self):
        patch = GraphPatch(action="approve", target_id="MATCH001")
        assert patch.persist_to_profile is False

    def test_modify_patch_with_value(self):
        patch = GraphPatch(
            action="modify",
            target_id="FACT001",
            new_value="Updated content",
            persist_to_profile=True,
        )
        assert patch.new_value == "Updated content"

    def test_invalid_action(self):
        with pytest.raises(ValidationError):
            GraphPatch(action="delete", target_id="X")
```

- [ ] **Step 2: Run to confirm current state (stubs may pass partially)**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_contracts.py -v 2>&1 | tail -20
```

- [ ] **Step 3: Rewrite `profile.py` with full content**

```python
# src/core/ai/generate_documents_v2/contracts/profile.py
"""Profile-side contracts: candidate knowledge graph and section strategy."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileEntry(BaseModel):
    """One experience or education item from the candidate profile."""

    id: str
    role: str = ""
    organization: str = ""
    achievements: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None


class EvidenceEdge(BaseModel):
    """Semantic relationship between two profile entries."""

    from_id: str
    to_id: str
    relation: str


class ProfileKG(BaseModel):
    """Persistent candidate knowledge graph (P1)."""

    entries: list[ProfileEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    evidence_edges: list[EvidenceEdge] = Field(default_factory=list)


class SectionMappingItem(BaseModel):
    """Strategy rule for one document section (P2)."""

    section_id: str
    target_document: str
    country_context: str = "global"
    mandatory: bool = True
    default_priority: int = Field(ge=1, le=5, default=3)
    style_guideline: str = ""
    default_fact_ids: list[str] = Field(default_factory=list)
    target_tone: str | None = None
```

- [ ] **Step 4: Run all contract tests**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_contracts.py -v
```

Expected: all pass (the stubs from Task 1 already have matching field names; Step 3 just adds docstrings)

- [ ] **Step 5: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/contracts/ tests/test_generate_documents_v2/test_contracts.py
git commit -m "feat: complete contract layer for generate_documents_v2 pipeline"
```

---

## Task 4: Artifact Storage (`PipelineArtifactStore`)

**Files:**
- Create: `src/core/ai/generate_documents_v2/storage.py`
- Create (inline in test): fixture data and storage tests

The store manages disk artifacts for the new pipeline using `DataManager`. Each pipeline run writes to `data/jobs/<source>/<job_id>/nodes/generate_documents_v2/<stage>/`.

- [ ] **Step 1: Add storage tests**

Add to `tests/test_generate_documents_v2/test_contracts.py` (or create a new file — here we use the same file for simplicity since it's still contract-adjacent):

Actually, create a new file:

```python
# tests/test_generate_documents_v2/test_storage.py
from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_write_and_load_job_kg(store, tmp_path):
    kg = JobKG(
        hard_requirements=[JobRequirement(id="R1", text="Python")],
        logistics=JobLogistics(location="Berlin"),
        company=CompanyData(name="TestCo"),
    )
    refs = store.write_stage("demo", "job-1", "job_kg", kg.model_dump())
    assert "job_kg_ref" in refs

    loaded = json.loads(
        (tmp_path / "demo/job-1/nodes/generate_documents_v2/job_kg/current.json").read_text()
    )
    assert loaded["hard_requirements"][0]["id"] == "R1"
    assert loaded["company"]["name"] == "TestCo"


def test_write_and_load_job_delta(store, tmp_path):
    delta = JobDelta(must_highlight_skills=["Rust", "Kafka"])
    refs = store.write_stage("demo", "job-2", "job_delta", delta.model_dump())
    assert "job_delta_ref" in refs

    loaded = json.loads(
        (tmp_path / "demo/job-2/nodes/generate_documents_v2/job_delta/current.json").read_text()
    )
    assert "Rust" in loaded["must_highlight_skills"]


def test_load_stage_returns_none_when_missing(store):
    result = store.load_stage("demo", "missing-job", "job_kg")
    assert result is None


def test_sha256_is_stable(store, tmp_path):
    kg = JobKG(hard_requirements=[JobRequirement(id="R1", text="Go")])
    store.write_stage("demo", "job-3", "job_kg", kg.model_dump())
    path = tmp_path / "demo/job-3/nodes/generate_documents_v2/job_kg/current.json"
    h1 = store.sha256_file(path)
    h2 = store.sha256_file(path)
    assert h1 == h2
    assert h1.startswith("sha256:")
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_storage.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError` for `storage`

- [ ] **Step 3: Implement `PipelineArtifactStore`**

```python
# src/core/ai/generate_documents_v2/storage.py
"""Artifact persistence for the generate_documents_v2 pipeline.

Each pipeline stage writes its output to:
  data/jobs/<source>/<job_id>/nodes/generate_documents_v2/<stage>/current.json

This mirrors the MatchArtifactStore pattern — JSON artifacts on disk,
DataManager handles atomic writes and path validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.data_manager import DataManager


class PipelineArtifactStore:
    """Manage per-stage JSON artifacts for the generate_documents_v2 pipeline."""

    def __init__(self, root: str | Path = "data/jobs") -> None:
        self.root = Path(root)
        self._dm = DataManager(self.root)

    def _stage_dir(self, source: str, job_id: str, stage: str) -> Path:
        return self.root / source / job_id / "nodes" / "generate_documents_v2" / stage

    def write_stage(
        self,
        source: str,
        job_id: str,
        stage: str,
        payload: dict[str, Any],
    ) -> dict[str, str]:
        """Write a stage artifact and return a ref dict keyed as ``{stage}_ref``."""
        path = self._stage_dir(source, job_id, stage) / "current.json"
        self._dm.write_json_path(path, payload)
        return {f"{stage}_ref": str(path)}

    def load_stage(
        self,
        source: str,
        job_id: str,
        stage: str,
    ) -> dict[str, Any] | None:
        """Load a stage artifact from disk. Returns None if not found."""
        path = self._stage_dir(source, job_id, stage) / "current.json"
        if not path.exists():
            return None
        return self._dm.read_json_path(path)

    def sha256_file(self, path: str | Path) -> str:
        """Return sha256:<hex> digest for a persisted artifact."""
        return self._dm.sha256_path(path)
```

- [ ] **Step 4: Run storage tests**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_storage.py -v
```

Expected: 4 tests pass

- [ ] **Step 5: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/storage.py tests/test_generate_documents_v2/test_storage.py
git commit -m "feat: PipelineArtifactStore for generate_documents_v2 stage persistence"
```

---

## Task 5: Profile Loader (`load_profile_kg`, `load_section_mapping`)

The profile loader reads `ProfileBaseData` (existing format in `src/core/profile.py`) from disk and produces the new `ProfileKG` and `SectionMappingItem` list needed by the pipeline. `SectionMapping` lives at `data/reference_data/profile/section_mapping.json`.

**Files:**
- Create: `src/core/ai/generate_documents_v2/profile_loader.py`
- Create: `data/reference_data/profile/section_mapping.json`
- Create: `tests/test_generate_documents_v2/test_profile_loader.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_generate_documents_v2/test_profile_loader.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.ai.generate_documents_v2.contracts.profile import (
    ProfileKG,
    SectionMappingItem,
)
from src.core.ai.generate_documents_v2.profile_loader import (
    load_profile_kg,
    load_section_mapping,
)

SAMPLE_PROFILE = {
    "owner": {
        "full_name": "Juan Pérez",
        "email": "juan@example.com",
        "phone": "+49 123 456",
    },
    "experience": [
        {
            "role": "Data Engineer",
            "organization": "ACME GmbH",
            "start_date": "2022-01",
            "end_date": "2024-12",
            "achievements": ["Built Kafka pipeline", "Reduced latency 40%"],
            "keywords": ["Kafka", "Python", "AWS"],
        }
    ],
    "skills": {
        "programming_languages": ["Python", "Rust"],
        "ml_ai": ["PyTorch"],
    },
    "cv_generation_context": {
        "tagline_seed": "Data engineering and Rust systems",
        "traits": ["railway-enthusiast", "curious"],
    },
}

SAMPLE_SECTION_MAPPING = [
    {
        "section_id": "summary",
        "target_document": "cv",
        "mandatory": True,
        "default_priority": 5,
    },
    {
        "section_id": "experience",
        "target_document": "cv",
        "mandatory": True,
        "default_priority": 4,
        "country_context": "global",
    },
]


def test_load_profile_kg_produces_entries(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE), encoding="utf-8")
    kg = load_profile_kg(profile_path)
    assert isinstance(kg, ProfileKG)
    assert len(kg.entries) == 1
    assert kg.entries[0].id == "EXP001"
    assert kg.entries[0].role == "Data Engineer"
    assert kg.entries[0].organization == "ACME GmbH"


def test_load_profile_kg_flattens_skills(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE), encoding="utf-8")
    kg = load_profile_kg(profile_path)
    assert "Python" in kg.skills
    assert "Rust" in kg.skills
    assert "PyTorch" in kg.skills


def test_load_profile_kg_extracts_traits(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE), encoding="utf-8")
    kg = load_profile_kg(profile_path)
    assert "railway-enthusiast" in kg.traits


def test_load_profile_kg_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_profile_kg(tmp_path / "nonexistent.json")


def test_load_section_mapping_returns_items(tmp_path):
    mapping_path = tmp_path / "section_mapping.json"
    mapping_path.write_text(json.dumps(SAMPLE_SECTION_MAPPING), encoding="utf-8")
    items = load_section_mapping(mapping_path)
    assert len(items) == 2
    assert isinstance(items[0], SectionMappingItem)
    assert items[0].section_id == "summary"


def test_load_section_mapping_missing_file_returns_empty(tmp_path):
    items = load_section_mapping(tmp_path / "missing.json")
    assert items == []
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_profile_loader.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `profile_loader.py`**

```python
# src/core/ai/generate_documents_v2/profile_loader.py
"""Load P1 (ProfileKG) and P2 (SectionMapping) from disk.

ProfileKG is derived from the existing ProfileBaseData JSON.
SectionMapping is a separate JSON list at data/reference_data/profile/section_mapping.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.core.ai.generate_documents_v2.contracts.profile import (
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)


def load_profile_kg(profile_path: str | Path) -> ProfileKG:
    """Build a ProfileKG from a ProfileBaseData JSON file.

    Args:
        profile_path: Absolute or relative path to the profile JSON.

    Returns:
        Populated ProfileKG ready for use in the pipeline.

    Raises:
        FileNotFoundError: If the profile file does not exist.
    """
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))

    entries = _build_entries(raw.get("experience", []))
    skills = _flatten_skills(raw.get("skills", {}))
    traits = _extract_traits(raw.get("cv_generation_context", {}))

    return ProfileKG(entries=entries, skills=skills, traits=traits)


def load_section_mapping(mapping_path: str | Path) -> list[SectionMappingItem]:
    """Load section mapping rules from a JSON file.

    Returns an empty list if the file does not exist — callers can fall back
    to a default strategy.

    Args:
        mapping_path: Path to section_mapping.json.
    """
    path = Path(mapping_path)
    if not path.exists():
        return []

    raw: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    return [SectionMappingItem.model_validate(item) for item in raw]


def _build_entries(experience: list[dict]) -> list[ProfileEntry]:
    entries = []
    for index, item in enumerate(experience, start=1):
        entries.append(
            ProfileEntry(
                id=item.get("id") or f"EXP{index:03d}",
                role=item.get("role", ""),
                organization=item.get("organization", ""),
                achievements=item.get("achievements", []),
                keywords=item.get("keywords", []),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
            )
        )
    return entries


def _flatten_skills(skills_dict: dict) -> list[str]:
    flat: list[str] = []
    for skill_list in skills_dict.values():
        if isinstance(skill_list, list):
            flat.extend(str(s) for s in skill_list if s)
    return flat


def _extract_traits(context: dict) -> list[str]:
    traits = context.get("traits", [])
    if isinstance(traits, list):
        return [str(t) for t in traits if t]
    return []
```

- [ ] **Step 4: Create canonical section mapping fixture**

```json
// data/reference_data/profile/section_mapping.json
[
  {
    "section_id": "summary",
    "target_document": "cv",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 5,
    "style_guideline": "Max 3 lines, factual and punchy",
    "target_tone": "professional"
  },
  {
    "section_id": "experience",
    "target_document": "cv",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 4,
    "style_guideline": "Achievement-first bullet points"
  },
  {
    "section_id": "education",
    "target_document": "cv",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 3
  },
  {
    "section_id": "skills",
    "target_document": "cv",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 3
  },
  {
    "section_id": "letter_intro",
    "target_document": "letter",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 5,
    "style_guideline": "Hook sentence + role identification"
  },
  {
    "section_id": "letter_core",
    "target_document": "letter",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 4,
    "style_guideline": "Technical argument aligned with top requirements"
  },
  {
    "section_id": "letter_fit",
    "target_document": "letter",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 3,
    "style_guideline": "Cultural and mission alignment"
  },
  {
    "section_id": "letter_close",
    "target_document": "letter",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 2
  },
  {
    "section_id": "email_body",
    "target_document": "email",
    "country_context": "global",
    "mandatory": true,
    "default_priority": 5,
    "style_guideline": "Max 2 lines, CTA and reference to attachments"
  }
]
```

- [ ] **Step 5: Run profile loader tests**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_profile_loader.py -v
```

Expected: 7 tests pass

- [ ] **Step 6: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/profile_loader.py \
        tests/test_generate_documents_v2/test_profile_loader.py \
        data/reference_data/profile/section_mapping.json
git commit -m "feat: profile_loader — load ProfileKG and SectionMapping from disk"
```

---

## Task 6: Ingestion Node (J1 → J2 / `JobKG`)

The ingestion node receives raw job text, calls an LLM chain with structured output → `JobKG`, persists to disk, and returns the KG in state.

**Files:**
- Create: `src/core/ai/generate_documents_v2/prompts/ingestion.py`
- Create: `src/core/ai/generate_documents_v2/nodes/ingestion.py`
- Create: `tests/test_generate_documents_v2/test_ingestion.py`

- [ ] **Step 1: Write ingestion node tests with a fake chain**

```python
# tests/test_generate_documents_v2/test_ingestion.py
from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.nodes.ingestion import run_ingestion
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


FAKE_JOB_KG = JobKG(
    hard_requirements=[
        JobRequirement(id="R1", text="Python 3.10+", category="hard", priority=5),
        JobRequirement(id="R2", text="Rust experience", category="hard", priority=4),
    ],
    soft_context=[
        JobRequirement(id="S1", text="Team player", category="soft", priority=2),
    ],
    logistics=JobLogistics(location="Munich", relocation=True),
    company=CompanyData(name="Deutsche Bahn AG", department="Data & Analytics"),
)


class FakeIngestionChain:
    def __init__(self, response: JobKG):
        self._response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> JobKG:
        self.calls.append(payload)
        return self._response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_ingestion_returns_job_kg(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    result = run_ingestion(
        source="demo",
        job_id="job-1",
        job_raw_text="We are looking for a Python and Rust engineer at Deutsche Bahn...",
        chain=chain,
        store=store,
    )
    assert "job_kg" in result
    kg = JobKG.model_validate(result["job_kg"])
    assert kg.company.name == "Deutsche Bahn AG"
    assert len(kg.hard_requirements) == 2


def test_run_ingestion_writes_to_disk(store, tmp_path):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    run_ingestion(
        source="demo",
        job_id="job-2",
        job_raw_text="Software Engineer position...",
        chain=chain,
        store=store,
    )
    stored = json.loads(
        (tmp_path / "demo/job-2/nodes/generate_documents_v2/job_kg/current.json").read_text()
    )
    assert stored["company"]["name"] == "Deutsche Bahn AG"


def test_run_ingestion_calls_chain_once(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    run_ingestion(
        source="demo",
        job_id="job-3",
        job_raw_text="some job text",
        chain=chain,
        store=store,
    )
    assert len(chain.calls) == 1


def test_run_ingestion_sets_status(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    result = run_ingestion(
        source="demo",
        job_id="job-4",
        job_raw_text="some text",
        chain=chain,
        store=store,
    )
    assert result.get("status") == "job_extracted"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_ingestion.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create ingestion prompts**

```python
# src/core/ai/generate_documents_v2/prompts/ingestion.py
"""Prompts for the ingestion node (J1 → J2 / JobKG)."""

from __future__ import annotations

INGESTION_SYSTEM_PROMPT = """You are a precise job-posting analyst.
Your task is to extract structured data from a raw job description.

Rules:
- Extract ONLY what is explicitly stated or strongly implied in the text.
- Separate hard technical requirements from soft cultural context.
- Assign realistic priority scores (1=low, 5=critical).
- Generate stable IDs: hard requirements as R01, R02...; soft as S01, S02...
- For logistics, extract location, remote policy, relocation, visa sponsorship only when mentioned.
- Do NOT invent requirements not present in the text.
"""


def build_ingestion_user_prompt(job_raw_text: str) -> str:
    return f"""Extract the structured job knowledge graph from this job posting.

JOB POSTING:
{job_raw_text}

Produce a JobKG with:
- hard_requirements: technical skills, experience, certifications explicitly required
- soft_context: culture, collaboration, growth mentions
- logistics: location, remote/hybrid, contract type, relocation support, visa sponsorship
- company: company name, hiring department, contact person if mentioned
"""
```

- [ ] **Step 4: Implement the ingestion node**

```python
# src/core/ai/generate_documents_v2/nodes/ingestion.py
"""Ingestion node: raw job text → structured JobKG (J1 → J2)."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.prompts.ingestion import (
    INGESTION_SYSTEM_PROMPT,
    build_ingestion_user_prompt,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def run_ingestion(
    *,
    source: str,
    job_id: str,
    job_raw_text: str,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Extract a structured JobKG from raw job text.

    Args:
        source: Job source identifier (e.g. "stepstone").
        job_id: Stable job identifier.
        job_raw_text: Full raw text of the job posting (J1).
        chain: LLM chain with structured output → JobKG.
        store: Artifact store for persistence.

    Returns:
        State update dict with ``job_kg`` (serialized) and ``status``.
    """
    logger.info(f"{LogTag.LLM} Ingestion: extracting JobKG for {source}/{job_id}")

    user_prompt = build_ingestion_user_prompt(job_raw_text)
    job_kg: JobKG = chain.invoke({"system": INGESTION_SYSTEM_PROMPT, "user": user_prompt})

    refs = store.write_stage(source, job_id, "job_kg", job_kg.model_dump())

    logger.info(
        f"{LogTag.OK} Ingestion complete: {len(job_kg.hard_requirements)} hard reqs, "
        f"{len(job_kg.soft_context)} soft reqs"
    )
    return {"job_kg": job_kg.model_dump(), "artifact_refs": refs, "status": "job_extracted"}


def build_ingestion_chain(model: Any | None = None) -> Any:
    """Build the LangChain chain for ingestion with structured output → JobKG."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    if not os.environ.get("GOOGLE_API_KEY"):
        return _demo_ingestion_chain()

    llm = model or ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    return prompt | llm.with_structured_output(JobKG)


class _demo_ingestion_chain:
    """Minimal demo chain when no API key is present."""

    def invoke(self, payload: dict) -> JobKG:
        from src.core.ai.generate_documents_v2.contracts.job import (
            CompanyData,
            JobLogistics,
            JobRequirement,
        )
        return JobKG(
            hard_requirements=[
                JobRequirement(id="R01", text="Demo requirement: Python", priority=4)
            ],
            logistics=JobLogistics(location="Demo City"),
            company=CompanyData(name="Demo Corp"),
        )
```

- [ ] **Step 5: Run ingestion tests**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_ingestion.py -v
```

Expected: 4 tests pass

- [ ] **Step 6: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/nodes/ingestion.py \
        src/core/ai/generate_documents_v2/prompts/ingestion.py \
        tests/test_generate_documents_v2/test_ingestion.py
git commit -m "feat: ingestion node J1→J2 with fake-chain tests"
```

---

## Task 7: Requirement Filter Node (J2 → J3 / `JobDelta`)

The requirement filter receives a `JobKG` and produces a `JobDelta` — the focused relevance signal for this specific application.

**Files:**
- Create: `src/core/ai/generate_documents_v2/prompts/requirement_filter.py`
- Create: `src/core/ai/generate_documents_v2/nodes/requirement_filter.py`
- Create: `tests/test_generate_documents_v2/test_requirement_filter.py`

- [ ] **Step 1: Write requirement filter tests**

```python
# tests/test_generate_documents_v2/test_requirement_filter.py
from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.nodes.requirement_filter import run_requirement_filter
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


SAMPLE_JOB_KG = JobKG(
    hard_requirements=[
        JobRequirement(id="R01", text="Rust 1.7+", priority=5),
        JobRequirement(id="R02", text="Python 3.10+", priority=4),
        JobRequirement(id="R03", text="Nice to have: Haskell", priority=1),
    ],
    soft_context=[
        JobRequirement(id="S01", text="Passion for rail transport", category="soft", priority=3),
    ],
    logistics=JobLogistics(location="Munich", relocation=True),
    company=CompanyData(name="Deutsche Bahn"),
)

FAKE_DELTA = JobDelta(
    must_highlight_skills=["Rust", "Python"],
    ignored_requirements=["Nice to have: Haskell"],
    soft_vibe_requirements=["Passion for rail transport"],
    logistics_flags={"relocation_relevant": True},
)


class FakeFilterChain:
    def __init__(self, response: JobDelta):
        self._response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> JobDelta:
        self.calls.append(payload)
        return self._response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_filter_returns_job_delta(store):
    chain = FakeFilterChain(FAKE_DELTA)
    result = run_requirement_filter(
        source="demo",
        job_id="job-1",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    assert "job_delta" in result
    delta = JobDelta.model_validate(result["job_delta"])
    assert "Rust" in delta.must_highlight_skills
    assert "Nice to have: Haskell" in delta.ignored_requirements


def test_run_filter_writes_to_disk(store, tmp_path):
    chain = FakeFilterChain(FAKE_DELTA)
    run_requirement_filter(
        source="demo",
        job_id="job-2",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    stored = json.loads(
        (tmp_path / "demo/job-2/nodes/generate_documents_v2/job_delta/current.json").read_text()
    )
    assert "Rust" in stored["must_highlight_skills"]


def test_run_filter_calls_chain_once(store):
    chain = FakeFilterChain(FAKE_DELTA)
    run_requirement_filter(
        source="demo",
        job_id="job-3",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    assert len(chain.calls) == 1


def test_run_filter_sets_status(store):
    chain = FakeFilterChain(FAKE_DELTA)
    result = run_requirement_filter(
        source="demo",
        job_id="job-4",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    assert result.get("status") == "requirements_filtered"


def test_run_filter_prompt_includes_kg_data(store):
    chain = FakeFilterChain(FAKE_DELTA)
    run_requirement_filter(
        source="demo",
        job_id="job-5",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    user_prompt = chain.calls[0]["user"]
    assert "Rust" in user_prompt
    assert "Munich" in user_prompt
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_requirement_filter.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create requirement filter prompts**

```python
# src/core/ai/generate_documents_v2/prompts/requirement_filter.py
"""Prompts for the requirement filter node (J2 → J3 / JobDelta)."""

from __future__ import annotations

import json

from src.core.ai.generate_documents_v2.contracts.job import JobKG

FILTER_SYSTEM_PROMPT = """You are a strategic job application advisor.
Given a structured job knowledge graph, decide what to emphasize and what to deprioritize.

Rules:
- must_highlight_skills: list the 3-5 most critical technical skills the application MUST demonstrate
- ignored_requirements: list requirements that are clearly secondary or "nice to have"
- soft_vibe_requirements: list cultural or personality signals worth reflecting in tone
- logistics_flags: boolean flags — set relocation_relevant=true if location change is required and relevant to mention
- custom_instructions: any specific tactical note for this application (e.g. mention visa status)
- Be decisive. An application that tries to address everything emphasizes nothing.
"""


def build_filter_user_prompt(job_kg: JobKG) -> str:
    hard = [
        f"[{r.id}] {r.text} (priority={r.priority})"
        for r in job_kg.hard_requirements
    ]
    soft = [f"[{r.id}] {r.text}" for r in job_kg.soft_context]
    logistics_parts = []
    if job_kg.logistics.location:
        logistics_parts.append(f"Location: {job_kg.logistics.location}")
    if job_kg.logistics.relocation:
        logistics_parts.append("Relocation offered")
    if job_kg.logistics.visa_sponsorship:
        logistics_parts.append("Visa sponsorship available")

    return f"""Analyze this job knowledge graph and produce a relevance delta.

HARD REQUIREMENTS:
{json.dumps(hard, indent=2)}

SOFT CONTEXT:
{json.dumps(soft, indent=2)}

LOGISTICS:
{chr(10).join(logistics_parts) if logistics_parts else "Not specified"}

COMPANY: {job_kg.company.name or "Unknown"}

Decide what to highlight, what to ignore, and any tactical flags for this application.
"""
```

- [ ] **Step 4: Implement the requirement filter node**

```python
# src/core/ai/generate_documents_v2/nodes/requirement_filter.py
"""Requirement filter node: JobKG → JobDelta (J2 → J3)."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.core.ai.generate_documents_v2.contracts.job import JobDelta, JobKG
from src.core.ai.generate_documents_v2.prompts.requirement_filter import (
    FILTER_SYSTEM_PROMPT,
    build_filter_user_prompt,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def run_requirement_filter(
    *,
    source: str,
    job_id: str,
    job_kg: JobKG,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Filter job requirements into a focused relevance delta.

    Args:
        source: Job source identifier.
        job_id: Stable job identifier.
        job_kg: Structured JobKG produced by the ingestion node.
        chain: LLM chain with structured output → JobDelta.
        store: Artifact store for persistence.

    Returns:
        State update dict with ``job_delta`` (serialized) and ``status``.
    """
    logger.info(f"{LogTag.LLM} RequirementFilter: filtering {source}/{job_id}")

    user_prompt = build_filter_user_prompt(job_kg)
    job_delta: JobDelta = chain.invoke({"system": FILTER_SYSTEM_PROMPT, "user": user_prompt})

    refs = store.write_stage(source, job_id, "job_delta", job_delta.model_dump())

    logger.info(
        f"{LogTag.OK} RequirementFilter done: "
        f"{len(job_delta.must_highlight_skills)} highlights, "
        f"{len(job_delta.ignored_requirements)} ignored"
    )
    return {
        "job_delta": job_delta.model_dump(),
        "artifact_refs": refs,
        "status": "requirements_filtered",
    }


def build_requirement_filter_chain(model: Any | None = None) -> Any:
    """Build the LangChain chain for requirement filtering with structured output."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    if not os.environ.get("GOOGLE_API_KEY"):
        return _demo_filter_chain()

    llm = model or ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    return prompt | llm.with_structured_output(JobDelta)


class _demo_filter_chain:
    """Minimal demo chain when no API key is present."""

    def invoke(self, payload: dict) -> JobDelta:
        return JobDelta(
            must_highlight_skills=["Demo Skill A", "Demo Skill B"],
            ignored_requirements=["Nice to have: Demo optional skill"],
        )
```

- [ ] **Step 5: Run requirement filter tests**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/test_requirement_filter.py -v
```

Expected: 5 tests pass

- [ ] **Step 6: Commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/nodes/requirement_filter.py \
        src/core/ai/generate_documents_v2/prompts/requirement_filter.py \
        tests/test_generate_documents_v2/test_requirement_filter.py
git commit -m "feat: requirement filter node J2→J3 with fake-chain tests"
```

---

## Task 8: Full Suite Verification & Module Export Cleanup

**Files:**
- Modify: `src/core/ai/generate_documents_v2/__init__.py`
- No new files

- [ ] **Step 1: Run the full new test suite**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/ -v
```

Expected: all tests pass (contracts, storage, profile_loader, ingestion, requirement_filter)

- [ ] **Step 2: Confirm existing tests are unbroken**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/ -q --ignore=tests/e2e 2>&1 | tail -10
```

Expected: same pass rate as before this plan. Zero regressions.

- [ ] **Step 3: Update top-level `__init__` for convenient imports**

```python
# src/core/ai/generate_documents_v2/__init__.py
"""generate_documents_v2 — new multi-stage document generation pipeline.

Stage 1 (this plan): Contracts, Storage, Profile Loader, Job Pipeline (J1→J2→J3).
Stage 2 (Plan 2):    Alignment Engine, Blueprint, Drafting.
Stage 3 (Plan 3):    Assembly, HITL graph wiring, Profile Updater.
"""

from src.core.ai.generate_documents_v2.profile_loader import (
    load_profile_kg,
    load_section_mapping,
)
from src.core.ai.generate_documents_v2.nodes.ingestion import (
    build_ingestion_chain,
    run_ingestion,
)
from src.core.ai.generate_documents_v2.nodes.requirement_filter import (
    build_requirement_filter_chain,
    run_requirement_filter,
)

__all__ = [
    "load_profile_kg",
    "load_section_mapping",
    "build_ingestion_chain",
    "run_ingestion",
    "build_requirement_filter_chain",
    "run_requirement_filter",
]
```

- [ ] **Step 4: Final run to confirm clean state**

```bash
cd /home/jp/postulator/podyulsyot3001
python -m pytest tests/test_generate_documents_v2/ -v --tb=short
```

Expected: all pass, zero warnings except the asyncio_default_fixture_loop_scope deprecation (pre-existing)

- [ ] **Step 5: Final commit**

```bash
cd /home/jp/postulator/podyulsyot3001
git add src/core/ai/generate_documents_v2/__init__.py
git commit -m "feat: Plan 1 complete — contracts, storage, profile loader, J1→J2→J3 job pipeline"
```

---

## Self-Review

### Spec Coverage Check

| Spec requirement | Covered by task |
|-----------------|----------------|
| `TextAnchor` with audit trail fields | Task 1 |
| `IdeaFact` with priority 1-5 and status enum | Task 1 |
| `ProfileKG` (entries, skills, traits, edges) | Task 1 + Task 3 + Task 5 |
| `SectionMapping` (P2) as persistent artifact | Task 5 |
| `JobKG` (J2) with hard/soft/logistics/company | Task 1 + Task 2 |
| `JobDelta` (J3) with highlights + ignores + flags | Task 2 |
| `MatchEdge`, `SectionBlueprint`, `GlobalBlueprint` | Task 1 stubs (implemented in Plan 2) |
| `DraftedSection` with auto word_count | Task 3 |
| `FinalMarkdownBundle` with canonical field names | Task 3 |
| `GraphPatch` with action enum | Task 3 |
| Artifact storage per-stage | Task 4 |
| Profile loader reads existing `ProfileBaseData` | Task 5 |
| Ingestion node J1→J2 with fake-chain tests | Task 6 |
| Requirement filter node J2→J3 with tests | Task 7 |
| Existing tests unbroken | Task 8 |

**Not covered in this plan (intentional — Plans 2 and 3):**
- Alignment Engine (replaces match_skill)
- Conciliator + GlobalBlueprint
- Redaction + Smoothing nodes
- Assembler (deterministic)
- HITL 1, 2, 3 graph interrupt points
- Profile Updater
- Regional strategies (German, Chilean, Academic)

### Type Consistency Check

- `run_ingestion` returns `dict[str, Any]` with keys `job_kg`, `artifact_refs`, `status` — consistent with how Plan 2 nodes will consume state
- `run_requirement_filter` takes a `JobKG` object (not raw dict) — callers must deserialize from state before calling; this is explicit and safe
- `PipelineArtifactStore.write_stage` returns `{f"{stage}_ref": str}` — consistent across all callers
- All contracts use `Field(default_factory=list)` for list fields — no mutable defaults

### Placeholder Scan

No TBDs, no TODOs, no "implement later" phrases found. All steps contain actual code.
