"""Localization node for drafted documents using the existing translator tool."""

from __future__ import annotations

from typing import Any

from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.core.tools.translator.providers.google.adapter import GoogleTranslatorAdapter


def run_localization(
    *,
    source: str,
    job_id: str,
    document: DraftedDocument,
    target_language: str,
    store: PipelineArtifactStore,
    translator: Any | None = None,
) -> dict[str, Any]:
    """Translate drafted markdown sections to the target language when needed."""

    if target_language == "en":
        localized = document
    else:
        adapter = translator or GoogleTranslatorAdapter()
        localized = DraftedDocument(
            doc_type=document.doc_type,
            sections_md={
                key: adapter.translate_text(
                    value, target_lang=target_language, source_lang="en"
                )
                for key, value in document.sections_md.items()
            },
            cohesion_score=document.cohesion_score,
        )

    refs = store.write_stage(
        source,
        job_id,
        f"localized_{document.doc_type}",
        localized.model_dump(),
    )
    return {
        "localized_document": localized.model_dump(),
        "artifact_refs": refs,
        "status": f"localized_{document.doc_type}",
    }
