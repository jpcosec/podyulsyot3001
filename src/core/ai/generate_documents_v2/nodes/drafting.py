"""Drafting node: blueprint -> DraftedDocument."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.core.ai.generate_documents_v2.contracts.blueprint import GlobalBlueprint
from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.prompts.drafting import (
    DRAFTING_SYSTEM_PROMPT,
    build_drafting_user_prompt,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


# TODO(future): extract to shared helper — see future_docs/issues/generate_documents_v2_google_api_key_duplication.md
def _google_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def run_drafting(
    *,
    source: str,
    job_id: str,
    doc_type: str,
    blueprint: GlobalBlueprint,
    chain: Any,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    logger.info(
        "%s Drafting: writing %s for %s/%s", LogTag.LLM, doc_type, source, job_id
    )
    user_prompt = build_drafting_user_prompt(doc_type, blueprint)
    drafted: DraftedDocument = chain.invoke(
        {"system": DRAFTING_SYSTEM_PROMPT, "user": user_prompt}
    )
    refs = store.write_stage(source, job_id, f"draft_{doc_type}", drafted.model_dump())
    return {
        "drafted_document": drafted.model_dump(),
        "artifact_refs": refs,
        "status": f"drafted_{doc_type}",
    }


def build_drafting_chain(model: Any | None = None) -> Any:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    api_key = _google_api_key()
    if not api_key:
        return _DemoDraftingChain()
    llm = model or ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=api_key
    )
    return prompt | llm.with_structured_output(DraftedDocument)


class _DemoDraftingChain:
    def invoke(self, payload: dict[str, str]) -> DraftedDocument:
        del payload
        return DraftedDocument(doc_type="cv", sections_md={"summary": "Demo summary."})
