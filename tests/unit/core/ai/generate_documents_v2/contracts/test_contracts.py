from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.core.ai.generate_documents_v2.contracts.assembly import (
    FinalMarkdownBundle,
    MarkdownDocument,
)
from src.core.ai.generate_documents_v2.contracts.base import IdeaFact, TextAnchor
from src.core.ai.generate_documents_v2.contracts.blueprint import (
    GlobalBlueprint,
    SectionBlueprint,
)
from src.core.ai.generate_documents_v2.contracts.drafting import (
    DraftedDocument,
    DraftedSection,
)
from src.core.ai.generate_documents_v2.contracts.hitl import GraphPatch
from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.contracts.profile import (
    EvidenceEdge,
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)


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
            TextAnchor(document_id="d", start_index=-1, end_index=10, exact_quote="x")

    def test_rejects_end_before_start(self):
        with pytest.raises(ValidationError):
            TextAnchor(document_id="d", start_index=20, end_index=5, exact_quote="x")


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
            IdeaFact(id="F1", provenance_refs=[], core_content="x", priority=6)

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
        assert kg.job_title_original is None
        assert kg.job_title_english is None
        assert kg.hard_requirements == []
        assert kg.soft_context == []
        assert kg.logistics.location is None
        assert kg.company.name is None

    def test_with_requirements(self):
        kg = JobKG(
            source_language="de",
            job_title_original="Dateningenieur",
            job_title_english="Data Engineer",
            hard_requirements=[JobRequirement(id="R1", text="Rust")],
            soft_context=[
                JobRequirement(id="S1", text="Team culture", category="soft")
            ],
            logistics=JobLogistics(location="Munich", relocation=True),
            company=CompanyData(name="Deutsche Bahn"),
        )
        assert len(kg.hard_requirements) == 1
        assert kg.job_title_english == "Data Engineer"
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


class TestProfileKG:
    def test_empty_profile_kg(self):
        kg = ProfileKG()
        assert kg.entries == []
        assert kg.skills == []

    def test_with_entries(self):
        kg = ProfileKG(
            entries=[
                ProfileEntry(id="EXP001", role="Data Engineer", organization="ACME")
            ],
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
            section_id="summary", raw_markdown="short", word_count=99
        )
        assert section.word_count == 99


class TestDraftedDocument:
    def test_valid(self):
        doc = DraftedDocument(doc_type="cv", sections_md={"summary": "Hello"})
        assert doc.cohesion_score == 1.0


class TestMarkdownDocument:
    def test_valid(self):
        doc = MarkdownDocument(doc_type="letter", body_markdown="# Letter")
        assert doc.header_data == {}
        assert doc.footer_data == {}


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


class TestSupportContracts:
    def test_evidence_edge(self):
        edge = EvidenceEdge(from_id="EXP001", to_id="SKILL001", relation="demonstrates")
        assert edge.relation == "demonstrates"
