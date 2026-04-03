"""Ingestion node: raw job text to structured JobKG (J1 -> J2)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from src.core.data_manager import DataManager
from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.prompts.ingestion import (
    INGESTION_SYSTEM_PROMPT,
    build_ingestion_user_prompt,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.core.tools.translator.providers.google.adapter import GoogleTranslatorAdapter
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


# TODO(future): extract to shared helper — see future_docs/issues/generate_documents_v2_google_api_key_duplication.md
def _google_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def run_ingestion(
    *,
    source: str,
    job_id: str,
    job_raw_text: str | None = None,
    job_bundle: dict[str, Any] | None = None,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Extract a structured JobKG from raw job text."""

    if not job_raw_text and not job_bundle:
        raise ValueError("job_raw_text or job_bundle is required")

    logger.info("%s Ingestion: extracting JobKG for %s/%s", LogTag.LLM, source, job_id)
    user_prompt = build_ingestion_user_prompt(
        job_raw_text=job_raw_text,
        job_bundle=job_bundle,
    )
    job_kg: JobKG = chain.invoke(
        {"system": INGESTION_SYSTEM_PROMPT, "user": user_prompt}
    )
    job_kg = _recover_empty_job_kg(job_kg, job_bundle)
    refs = store.write_stage(source, job_id, "job_kg", job_kg.model_dump())
    logger.info(
        "%s Ingestion complete: %s hard reqs, %s soft reqs",
        LogTag.OK,
        len(job_kg.hard_requirements),
        len(job_kg.soft_context),
    )
    return {
        "job_kg": job_kg.model_dump(),
        "artifact_refs": refs,
        "status": "job_extracted",
    }


def load_ingestion_artifact_bundle(
    *,
    source: str,
    job_id: str,
    jobs_root: str | Path = "data/jobs",
) -> dict[str, Any]:
    """Load the minimal ingest bundle used by the v2 ingestion node."""

    dm = DataManager(jobs_root)
    ingest_dir = dm.node_stage_dir(source, job_id, "ingest", "proposed")
    bundle: dict[str, Any] = {}
    for filename, key in (
        ("state.json", "state"),
        ("listing.json", "listing"),
        ("listing_case.json", "listing_case"),
    ):
        path = ingest_dir / filename
        if path.exists():
            bundle[key] = dm.read_json_path(path)

    if not bundle:
        raise FileNotFoundError(f"No ingest artifacts found for {source}/{job_id}")
    return bundle


def build_ingestion_chain(model: Any | None = None) -> Any:
    """Build the LangChain chain for ingestion with structured output."""

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    api_key = _google_api_key()
    if not api_key:
        return _DemoIngestionChain()

    llm = model or ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
    )
    return prompt | llm.with_structured_output(JobKG)


class _DemoIngestionChain:
    """Minimal demo chain when no API key is present."""

    def invoke(self, payload: dict[str, str]) -> JobKG:
        """Return a deterministic demo JobKG when no API key exists."""
        del payload

        return JobKG(
            source_language="en",
            job_title_original="Demo Role",
            job_title_english="Demo Role",
            hard_requirements=[
                JobRequirement(id="R01", text="Demo requirement: Python", priority=4)
            ],
            logistics=JobLogistics(location="Demo City"),
            company=CompanyData(name="Demo Corp"),
        )


def _recover_empty_job_kg(job_kg: JobKG, job_bundle: dict[str, Any] | None) -> JobKG:
    if not job_bundle or job_kg.hard_requirements:
        return job_kg

    state = job_bundle.get("state", {})
    requirements = state.get("requirements", [])
    if not requirements:
        return job_kg

    source_language = state.get("original_language") or "auto"
    translator = GoogleTranslatorAdapter()
    translated_requirements: list[JobRequirement] = []
    for index, requirement in enumerate(requirements, start=1):
        text = str(requirement).strip()
        if not text:
            continue
        try:
            english_text = translator.translate_text(
                text,
                target_lang="en",
                source_lang=source_language,
            )
        except Exception:
            english_text = text
        translated_requirements.append(
            JobRequirement(id=f"R{index:02d}", text=english_text, priority=4)
        )

    if not translated_requirements:
        return job_kg

    return JobKG(
        source_language=state.get("original_language"),
        job_title_original=state.get("job_title"),
        job_title_english=job_kg.job_title_english or state.get("job_title"),
        hard_requirements=translated_requirements,
        soft_context=job_kg.soft_context,
        logistics=job_kg.logistics
        if any(job_kg.logistics.model_dump().values())
        else JobLogistics(
            location=state.get("location"),
            remote=_detect_remote(state.get("remote_policy")),
            contract_type=state.get("employment_type"),
        ),
        company=job_kg.company
        if any(job_kg.company.model_dump().values())
        else CompanyData(name=state.get("company_name")),
        source_anchors=job_kg.source_anchors,
    )


def _detect_remote(remote_policy: Any) -> bool | None:
    if not remote_policy:
        return None
    text = str(remote_policy).lower()
    if "remote" in text or "homeoffice" in text:
        return True
    return None
