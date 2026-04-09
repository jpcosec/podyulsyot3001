"""Alignment node: ProfileKG + JobKG -> MatchEdge list."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import ProfileKG
from src.core.ai.generate_documents_v2.prompts.alignment import (
    ALIGNMENT_SYSTEM_PROMPT,
    build_alignment_user_prompt,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

from ._utils import _gemini_model, _google_api_key

logger = logging.getLogger(__name__)


class MatchResult(BaseModel):
    """Structured output returned by the alignment chain."""

    matches: list[MatchEdge] = Field(default_factory=list)


def run_alignment(
    *,
    source: str,
    job_id: str,
    profile_kg: ProfileKG,
    job_kg: JobKG,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Run profile-to-job alignment and persist the resulting matches.

    Args:
        source: Source name for artifact placement.
        job_id: Job identifier for artifact placement.
        profile_kg: Canonical profile knowledge graph.
        job_kg: Canonical job knowledge graph.
        chain: Structured-output chain used for alignment.
        store: Artifact store for stage persistence.

    Returns:
        Serialized matches plus artifact refs and a stage status string.
    """
    logger.info("%s Alignment: matching profile to %s/%s", LogTag.LLM, source, job_id)
    user_prompt = build_alignment_user_prompt(profile_kg, job_kg)
    result: MatchResult = chain.invoke(
        {"system": ALIGNMENT_SYSTEM_PROMPT, "user": user_prompt}
    )
    payload = {"matches": [item.model_dump() for item in result.matches]}
    refs = store.write_stage(source, job_id, "match_edges", payload)
    return {"matches": payload["matches"], "artifact_refs": refs, "status": "aligned"}


def build_alignment_chain(model: Any | None = None) -> Any:
    """Build the alignment chain or a demo fallback when no API key exists.

    Args:
        model: Optional preconfigured chat model.

    Returns:
        A chain compatible with ``run_alignment``.
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    api_key = _google_api_key()
    if not api_key:
        return _DemoAlignmentChain()
    llm = model or ChatGoogleGenerativeAI(
        model=_gemini_model("alignment"), google_api_key=api_key
    )
    return prompt | llm.with_structured_output(MatchResult)


class _DemoAlignmentChain:
    def invoke(self, payload: dict[str, str]) -> MatchResult:
        """Return a deterministic demo alignment result when no API key exists."""
        del payload
        return MatchResult(
            matches=[
                MatchEdge(
                    requirement_id="R01",
                    profile_evidence_ids=["EXP001"],
                    match_score=0.8,
                    reasoning="Profile experience demonstrates the required skill.",
                )
            ]
        )
