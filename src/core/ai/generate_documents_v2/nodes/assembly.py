"""Deterministic assembly helpers for Markdown bundle output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.data_manager import DataManager
from src.core.ai.generate_documents_v2.contracts.assembly import (
    FinalMarkdownBundle,
    MarkdownDocument,
)
from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


def _join_sections(document: DraftedDocument) -> str:
    return "\n\n".join(document.sections_md.values()).strip()


def assemble_markdown_document(
    *,
    document: DraftedDocument,
    job_kg: JobKG,
    profile_data: dict[str, Any] | None = None,
) -> MarkdownDocument:
    """Assemble one drafted document into a MarkdownDocument payload.

    Args:
        document: Drafted document content.
        job_kg: Job context used for lightweight header data.
        profile_data: Optional profile data used to build rich CV markdown.

    Returns:
        The assembled markdown document payload.
    """
    title = (
        job_kg.job_title_original or job_kg.job_title_english or "Application Document"
    )
    header = {"job_title": title, "company_name": job_kg.company.name}
    body = (
        _build_cv_markdown(document, profile_data)
        if document.doc_type == "cv"
        else _join_sections(document)
    )
    return MarkdownDocument(
        doc_type=document.doc_type, header_data=header, body_markdown=body
    )


def run_assembly(
    *,
    source: str,
    job_id: str,
    job_kg: JobKG,
    cv_document: DraftedDocument,
    letter_document: DraftedDocument,
    email_document: DraftedDocument,
    profile_data: dict[str, Any] | None = None,
    target_language: str = "en",
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Assemble final Markdown outputs and persist render inputs.

    Args:
        source: Source name for artifact placement.
        job_id: Job identifier for artifact placement.
        job_kg: Canonical job context for assembly metadata.
        cv_document: Drafted CV document.
        letter_document: Drafted letter document.
        email_document: Drafted email document.
        profile_data: Optional profile data used for CV enrichment.
        target_language: Target language suffix used for persisted files.
        store: Artifact store for stage persistence.

    Returns:
        Serialized markdown bundle plus artifact refs and status.
    """
    data_manager = DataManager(store.root)
    cv = assemble_markdown_document(
        document=cv_document, job_kg=job_kg, profile_data=profile_data
    )
    letter = assemble_markdown_document(document=letter_document, job_kg=job_kg)
    email = assemble_markdown_document(document=email_document, job_kg=job_kg)
    bundle = FinalMarkdownBundle(
        cv_full_md=cv.body_markdown,
        letter_full_md=letter.body_markdown,
        email_body_md=email.body_markdown,
        rendering_metadata={
            "job_title_original": job_kg.job_title_original,
            "job_title_english": job_kg.job_title_english,
            "company_name": job_kg.company.name,
        },
    )
    refs = store.write_stage(source, job_id, "markdown_bundle", bundle.model_dump())
    refs.update(
        _persist_render_inputs(
            data_manager=data_manager,
            source=source,
            job_id=job_id,
            target_language=target_language,
            bundle=bundle,
        )
    )
    return {
        "markdown_bundle": bundle.model_dump(),
        "artifact_refs": refs,
        "status": "assembled",
    }


def _persist_render_inputs(
    *,
    data_manager: DataManager,
    source: str,
    job_id: str,
    target_language: str,
    bundle: FinalMarkdownBundle,
) -> dict[str, str]:
    refs: dict[str, str] = {}
    files = {
        f"cv.{target_language}.md": bundle.cv_full_md,
        f"cover_letter.{target_language}.md": bundle.letter_full_md,
        f"email_body.{target_language}.md": bundle.email_body_md,
        "cv.md": bundle.cv_full_md,
        "cover_letter.md": bundle.letter_full_md,
        "email_body.txt": bundle.email_body_md,
    }
    for node_name in ("generate_documents_v2", "generate_documents"):
        for filename, content in files.items():
            path = data_manager.write_text_artifact(
                source=source,
                job_id=job_id,
                node_name=node_name,
                stage="proposed",
                filename=filename,
                content=content,
            )
            refs[f"{node_name}_{filename}"] = str(path)
            if (
                node_name == "generate_documents"
                and filename == f"cv.{target_language}.md"
            ):
                refs["cv_markdown_ref"] = str(path)
            if (
                node_name == "generate_documents"
                and filename == f"cover_letter.{target_language}.md"
            ):
                refs["letter_markdown_ref"] = str(path)
            if node_name == "generate_documents" and filename == "email_body.txt":
                refs["email_markdown_ref"] = str(path)
    return refs


def _build_cv_markdown(
    document: DraftedDocument,
    profile_data: dict[str, Any] | None,
) -> str:
    if not profile_data:
        return _strip_headings(_join_sections(document))

    parts: list[str] = []
    summary = _strip_headings(document.sections_md.get("summary", "")).strip()
    if summary:
        parts.append(summary)

    for experience in profile_data.get("experience", []):
        bullets = "\n".join(
            f"- {item}" for item in experience.get("achievements", []) if item
        )
        parts.append(
            "\n".join(
                [
                    f'::: {{.job role="{_escape_attr(experience.get("role", ""))}" org="{_escape_attr(experience.get("organization", ""))}" dates="{_format_dates(experience)}" location="{_escape_attr(experience.get("location", ""))}"}}',
                    bullets,
                    ":::",
                ]
            ).strip()
        )

    for education in profile_data.get("education", []):
        detail_lines = []
        if education.get("equivalency_note"):
            detail_lines.append(f"- {education['equivalency_note']}")
        if education.get("grade"):
            detail_lines.append(f"- Grade: {education['grade']}")
        parts.append(
            "\n".join(
                [
                    f'::: {{.education degree="{_escape_attr(education.get("degree", ""))}" specialization="{_escape_attr(education.get("specialization", ""))}" institution="{_escape_attr(education.get("institution", ""))}" dates="{_format_dates(education)}" location="{_escape_attr(education.get("location", ""))}"}}',
                    *detail_lines,
                    ":::",
                ]
            ).strip()
        )

    skill_lines = []
    for category, values in profile_data.get("skills", {}).items():
        if values:
            skill_lines.append(
                f"- **{category.replace('_', ' ').title()}:** {', '.join(values)}"
            )
    if skill_lines:
        parts.append("\n".join(skill_lines))

    return "\n\n".join(part for part in parts if part.strip()).strip()


def _strip_headings(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            lines.append(stripped.lstrip("#").strip())
        else:
            lines.append(line)
    return "\n".join(lines).strip()


def _format_dates(item: dict[str, Any]) -> str:
    start = item.get("start_date") or ""
    end = item.get("end_date") or "Present"
    joined = " - ".join(part for part in (start, end) if part)
    return _escape_attr(joined)


def _escape_attr(value: str) -> str:
    return str(value).replace('"', "'")
