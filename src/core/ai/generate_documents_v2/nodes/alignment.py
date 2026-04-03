"""Alignment node: ProfileKG + JobKG -> MatchEdge list."""

from __future__ import annotations

import logging
import os
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

logger = logging.getLogger(__name__)


class MatchResult(BaseModel):
    matches: list[MatchEdge] = Field(default_factory=list)


# TODO(future): extract to shared helper — see future_docs/issues/generate_documents_v2_google_api_key_duplication.md
def _google_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def run_alignment(
    *,
    source: str,
    job_id: str,
    profile_kg: ProfileKG,
    job_kg: JobKG,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    logger.info("%s Alignment: matching profile to %s/%s", LogTag.LLM, source, job_id)
    user_prompt = build_alignment_user_prompt(profile_kg, job_kg)
    result: MatchResult = chain.invoke(
        {"system": ALIGNMENT_SYSTEM_PROMPT, "user": user_prompt}
    )
    payload = {"matches": [item.model_dump() for item in result.matches]}
    refs = store.write_stage(source, job_id, "match_edges", payload)
    return {"matches": payload["matches"], "artifact_refs": refs, "status": "aligned"}


def build_alignment_chain(model: Any | None = None) -> Any:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    api_key = _google_api_key()
    if not api_key:
        return _DemoAlignmentChain()
    llm = model or ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=api_key
    )
    return prompt | llm.with_structured_output(MatchResult)


class _DemoAlignmentChain:
    def invoke(self, payload: dict[str, str]) -> MatchResult:
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
