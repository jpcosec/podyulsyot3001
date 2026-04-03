"""Requirement filter node: JobKG to JobDelta (J2 -> J3)."""

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


# TODO(future): extract to shared helper — see future_docs/issues/generate_documents_v2_google_api_key_duplication.md
def _google_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def run_requirement_filter(
    *,
    source: str,
    job_id: str,
    job_kg: JobKG,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Filter job requirements into a focused relevance delta."""

    logger.info("%s RequirementFilter: filtering %s/%s", LogTag.LLM, source, job_id)
    user_prompt = build_filter_user_prompt(job_kg)
    job_delta: JobDelta = chain.invoke(
        {"system": FILTER_SYSTEM_PROMPT, "user": user_prompt}
    )
    refs = store.write_stage(source, job_id, "job_delta", job_delta.model_dump())
    logger.info(
        "%s RequirementFilter done: %s highlights, %s ignored",
        LogTag.OK,
        len(job_delta.must_highlight_skills),
        len(job_delta.ignored_requirements),
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
    api_key = _google_api_key()
    if not api_key:
        return _DemoFilterChain()

    llm = model or ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
    )
    return prompt | llm.with_structured_output(JobDelta)


class _DemoFilterChain:
    """Minimal demo chain when no API key is present."""

    def invoke(self, payload: dict[str, str]) -> JobDelta:
        """Return a deterministic demo job delta when no API key exists."""
        del payload
        return JobDelta(
            must_highlight_skills=["Demo Skill A", "Demo Skill B"],
            ignored_requirements=["Nice to have: Demo optional skill"],
        )
