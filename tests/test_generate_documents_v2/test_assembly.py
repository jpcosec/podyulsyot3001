from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.contracts.job import CompanyData, JobKG
from src.core.ai.generate_documents_v2.nodes.assembly import (
    assemble_markdown_document,
    run_assembly,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


JOB = JobKG(
    job_title_original="Data Scientist / KI-Expert (w/m/d)",
    job_title_english="Data Scientist / AI Expert",
    company=CompanyData(name="Starpool Finanz GmbH"),
)


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_assemble_markdown_document_uses_job_metadata():
    doc = DraftedDocument(doc_type="cv", sections_md={"summary": "Strong fit."})
    markdown = assemble_markdown_document(document=doc, job_kg=JOB)
    assert markdown.header_data["job_title"] == "Data Scientist / KI-Expert (w/m/d)"
    assert markdown.header_data["company_name"] == "Starpool Finanz GmbH"


def test_run_assembly_returns_bundle(store):
    cv = DraftedDocument(doc_type="cv", sections_md={"summary": "CV summary"})
    letter = DraftedDocument(doc_type="letter", sections_md={"intro": "Letter intro"})
    email = DraftedDocument(doc_type="email", sections_md={"body": "Email body"})
    result = run_assembly(
        source="demo",
        job_id="job-1",
        job_kg=JOB,
        cv_document=cv,
        letter_document=letter,
        email_document=email,
        target_language="en",
        store=store,
    )
    assert result["status"] == "assembled"
    assert result["markdown_bundle"]["cv_full_md"] == "CV summary"
    assert "generate_documents_cv.en.md" in result["artifact_refs"]


def test_run_assembly_writes_disk(store, tmp_path):
    cv = DraftedDocument(doc_type="cv", sections_md={"summary": "CV summary"})
    letter = DraftedDocument(doc_type="letter", sections_md={"intro": "Letter intro"})
    email = DraftedDocument(doc_type="email", sections_md={"body": "Email body"})
    run_assembly(
        source="demo",
        job_id="job-2",
        job_kg=JOB,
        cv_document=cv,
        letter_document=letter,
        email_document=email,
        target_language="en",
        store=store,
    )
    payload = json.loads(
        (
            tmp_path
            / "demo/job-2/nodes/generate_documents_v2/markdown_bundle/current.json"
        ).read_text()
    )
    assert (
        payload["rendering_metadata"]["job_title_english"]
        == "Data Scientist / AI Expert"
    )
    assert (tmp_path / "demo/job-2/nodes/generate_documents/proposed/cv.en.md").exists()
