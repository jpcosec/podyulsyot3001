"""End-to-end helpers for the generate_documents_v2 pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.data_manager import DataManager
from src.core.ai.generate_documents_v2.contracts.blueprint import GlobalBlueprint
from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.contracts.job import JobDelta, JobKG
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.nodes.alignment import (
    build_alignment_chain,
    run_alignment,
)
from src.core.ai.generate_documents_v2.nodes.assembly import run_assembly
from src.core.ai.generate_documents_v2.nodes.blueprint import (
    build_blueprint_chain,
    run_blueprint,
)
from src.core.ai.generate_documents_v2.nodes.drafting import (
    build_drafting_chain,
    run_drafting,
)
from src.core.ai.generate_documents_v2.nodes.ingestion import (
    build_ingestion_chain,
    load_ingestion_artifact_bundle,
    run_ingestion,
)
from src.core.ai.generate_documents_v2.nodes.requirement_filter import (
    build_requirement_filter_chain,
    run_requirement_filter,
)
from src.core.ai.generate_documents_v2.profile_loader import (
    filter_sections_by_strategy,
    load_profile_kg,
    load_section_mapping,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.core.ai.generate_documents_v2.strategies import select_strategy


def generate_application_documents(
    *,
    source: str,
    job_id: str,
    profile_path: str | Path,
    section_mapping_path: str
    | Path = "data/reference_data/profile/section_mapping.json",
    target_language: str = "en",
    strategy_type: str = "professional",
    store: PipelineArtifactStore | None = None,
) -> dict[str, Any]:
    """Run the v2 document pipeline end-to-end."""

    artifact_store = store or PipelineArtifactStore()
    raw_profile = DataManager().read_json_path(Path(profile_path))
    bundle = load_ingestion_artifact_bundle(
        source=source,
        job_id=job_id,
        jobs_root=artifact_store.root,
    )
    profile_kg = load_profile_kg(profile_path)
    section_mapping = load_section_mapping(section_mapping_path)

    ingestion = run_ingestion(
        source=source,
        job_id=job_id,
        job_bundle=bundle,
        chain=build_ingestion_chain(),
        store=artifact_store,
    )
    job_kg = JobKG.model_validate(ingestion["job_kg"])

    filtering = run_requirement_filter(
        source=source,
        job_id=job_id,
        job_kg=job_kg,
        chain=build_requirement_filter_chain(),
        store=artifact_store,
    )
    job_delta = JobDelta.model_validate(filtering["job_delta"])

    alignment = run_alignment(
        source=source,
        job_id=job_id,
        profile_kg=profile_kg,
        job_kg=job_kg,
        chain=build_alignment_chain(),
        store=artifact_store,
    )
    matches = [MatchEdge.model_validate(item) for item in alignment["matches"]]

    strategy = select_strategy(strategy_type, target_language)
    filtered_mapping = filter_sections_by_strategy(section_mapping, strategy)

    blueprint_state = run_blueprint(
        source=source,
        job_id=job_id,
        application_id=f"{source}-{job_id}",
        strategy_type=strategy_type,
        chosen_strategy=strategy.name,
        section_order=strategy.section_order,
        section_mapping=filtered_mapping,
        job_delta=job_delta,
        matches=matches,
        chain=build_blueprint_chain(),
        store=artifact_store,
        job_kg=job_kg,
    )
    blueprint = GlobalBlueprint.model_validate(blueprint_state["blueprint"])

    chain = build_drafting_chain()
    drafts = {
        doc_type: DraftedDocument.model_validate(
            run_drafting(
                source=source,
                job_id=job_id,
                doc_type=doc_type,
                blueprint=blueprint,
                chain=chain,
                store=artifact_store,
            )["drafted_document"]
        )
        for doc_type in ("cv", "letter", "email")
    }

    assembly = run_assembly(
        source=source,
        job_id=job_id,
        job_kg=job_kg,
        cv_document=drafts["cv"],
        letter_document=drafts["letter"],
        email_document=drafts["email"],
        profile_data=raw_profile,
        target_language=target_language,
        store=artifact_store,
    )

    return {
        "job_kg": job_kg.model_dump(),
        "job_delta": job_delta.model_dump(),
        "matches": [match.model_dump() for match in matches],
        "blueprint": blueprint.model_dump(),
        "drafts": {key: value.model_dump() for key, value in drafts.items()},
        "markdown_bundle": assembly["markdown_bundle"],
        "artifact_refs": assembly["artifact_refs"],
        "status": "assembled",
    }

