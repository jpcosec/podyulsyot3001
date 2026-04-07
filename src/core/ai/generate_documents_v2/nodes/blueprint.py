"""Blueprint node: section strategy + delta + matches -> GlobalBlueprint."""

from __future__ import annotations

import logging
from typing import Any

from src.core.ai.generate_documents_v2.contracts.blueprint import GlobalBlueprint
from src.core.ai.generate_documents_v2.contracts.job import JobDelta, JobKG
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import SectionMappingItem
from src.core.ai.generate_documents_v2.prompts.blueprint import (
    BLUEPRINT_SYSTEM_PROMPT,
    build_blueprint_user_prompt,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

from ._utils import _google_api_key

logger = logging.getLogger(__name__)


def run_blueprint(
    *,
    source: str,
    job_id: str,
    application_id: str,
    strategy_type: str,
    chosen_strategy: str,
    section_order: list[str],
    section_mapping: list[SectionMappingItem],
    job_delta: JobDelta,
    matches: list[MatchEdge],
    chain: Any,
    store: PipelineArtifactStore,
    job_kg: JobKG | None = None,
) -> dict[str, Any]:
    """Run macroplanning and persist a serialized global blueprint.

    Args:
        source: Source name for artifact placement.
        job_id: Job identifier for artifact placement.
        application_id: Stable application identifier.
        strategy_type: Raw strategy name from state (forwarded to prompt).
        chosen_strategy: Resolved strategy name from ``select_strategy``.
        section_order: Preferred section ordering from the resolved strategy.
        section_mapping: Section mapping configuration (pre-filtered by strategy).
        job_delta: Focused job delta from requirement filtering.
        matches: Match edges produced by alignment.
        chain: Structured-output chain used for blueprint generation.
        store: Artifact store for stage persistence.
        job_kg: Optional job knowledge graph for extra context fields.

    Returns:
        Serialized blueprint plus artifact refs and stage status.
    """
    logger.info(
        "%s Blueprint: planning sections for %s/%s (strategy=%s)",
        LogTag.LLM, source, job_id, chosen_strategy,
    )
    job_title = (
        job_kg.job_title_original or job_kg.job_title_english if job_kg else None
    )
    user_prompt = build_blueprint_user_prompt(
        application_id=application_id,
        strategy_type=strategy_type,
        section_mapping=section_mapping,
        job_delta=job_delta,
        matches=matches,
        job_title=job_title,
        source=source,
    )
    blueprint: GlobalBlueprint = chain.invoke(
        {"system": BLUEPRINT_SYSTEM_PROMPT, "user": user_prompt}
    )
    # Preserve context fields and record the resolved strategy
    blueprint.job_title = job_title
    blueprint.source = source
    blueprint.chosen_strategy = chosen_strategy

    refs = store.write_stage(source, job_id, "blueprint", blueprint.model_dump())
    return {
        "blueprint": blueprint.model_dump(),
        "artifact_refs": refs,
        "status": "blueprinted",
    }


def build_blueprint_chain(model: Any | None = None) -> Any:
    """Build the blueprint generation chain or a deterministic demo fallback.

    Args:
        model: Optional preconfigured chat model.

    Returns:
        A chain compatible with ``run_blueprint``.
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), ("user", "{user}")]
    )
    api_key = _google_api_key()
    if not api_key:
        return _DemoBlueprintChain()
    llm = model or ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=api_key
    )
    return prompt | llm.with_structured_output(GlobalBlueprint)


class _DemoBlueprintChain:
    def invoke(self, payload: dict[str, str]) -> GlobalBlueprint:
        """Return a deterministic demo blueprint when no API key exists."""
        del payload
        from src.core.ai.generate_documents_v2.contracts.blueprint import (
            SectionBlueprint,
        )

        return GlobalBlueprint(
            application_id="demo",
            strategy_type="professional",
            chosen_strategy="generic",
            sections=[
                SectionBlueprint(
                    section_id="summary",
                    logical_train_of_thought=["EXP001", "R01"],
                    section_intent="Lead with relevant technical fit.",
                )
            ],
        )
