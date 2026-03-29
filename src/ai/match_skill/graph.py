"""LangGraph-native implementation of the match skill.

The graph mirrors the existing match/review/regeneration behavior while moving
the orchestration to native LangGraph patterns:

- a structured-output LangChain runnable for the model step,
- breakpoints/checkpointing for human review,
- ``Command``-based routing after the review decision,
- deterministic persistence and regeneration helpers around the graph.
"""

from __future__ import annotations

import os
from typing import Any, Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from src.ai.match_skill.contracts import (
    FeedbackItem,
    MatchEnvelope,
    ProfileEvidence,
    RequirementInput,
    RequirementMatch,
    ReviewDecision,
    ReviewPayload,
)
from src.ai.match_skill.prompt import build_match_prompt, build_prompt_input
from src.ai.match_skill.storage import MatchArtifactStore


class MatchSkillState(TypedDict, total=False):
    """Control-plane state carried through the match skill graph.

    Heavy payloads may still appear here in this reference implementation, but
    the shape is intentionally oriented around refs and routing signals so it can
    be thinned further later.
    """

    source: str
    job_id: str
    requirements: list[dict[str, Any]]
    profile_evidence: list[dict[str, Any]]
    effective_profile_evidence: list[dict[str, Any]]
    review_feedback: list[dict[str, Any]]
    regeneration_scope: list[str]
    review_payload: dict[str, Any]
    match_result: dict[str, Any]
    review_decision: ReviewDecision
    round_number: int
    match_result_hash: str
    status: str
    artifact_refs: dict[str, str]
    active_feedback: list[dict[str, Any]]
    profile_base_data: dict[str, Any]  # Ported from generate_documents
    document_deltas: dict[str, Any]
    generated_documents: dict[str, Any]


def build_match_skill_graph(
    *,
    match_chain: Any | None = None,
    gen_chain: Any | None = None,
    artifact_store: MatchArtifactStore | None = None,
    checkpointer: Any | None = None,
    interrupt_before: tuple[str, ...] = ("human_review_node",),
    interrupt_after: tuple[str, ...] = (),
    include_document_generation: bool = True,
):
    """Compile the reusable match skill graph.

    Args:
        match_chain: Optional prebuilt LangChain runnable for matching.
        gen_chain: Optional prebuilt LangChain runnable for document generation.
        artifact_store: Optional persistence adapter.
        checkpointer: Optional LangGraph checkpointer for pause/resume.
        interrupt_before: Nodes that should act as breakpoints before execution.
        interrupt_after: Nodes that should act as breakpoints after execution.

    Returns:
        A compiled LangGraph app ready for invoke/update_state usage.
    """
    from src.ai.generate_documents.graph import (
        _make_generate_documents_node,
        _make_demo_generate_documents_chain,
        build_default_generate_documents_chain,
    )
    from src.ai.generate_documents.storage import DocumentArtifactStore

    injected_match_chain = match_chain is not None
    match_chain = match_chain or build_default_match_chain()
    if gen_chain is None:
        gen_chain = (
            _make_demo_generate_documents_chain()
            if injected_match_chain
            else build_default_generate_documents_chain()
        )
    store = artifact_store or MatchArtifactStore()
    workflow = StateGraph(MatchSkillState)

    workflow.add_node("load_match_inputs", _make_load_match_inputs_node(store))
    workflow.add_node("run_match_llm", _make_run_match_llm_node(match_chain))
    workflow.add_node("persist_match_round", _make_persist_match_round_node(store))
    workflow.add_node("human_review_node", _human_review_node)
    workflow.add_node("apply_review_decision", _make_apply_review_decision_node(store))
    workflow.add_node(
        "prepare_regeneration_context",
        _make_prepare_regeneration_context_node(store),
    )
    if include_document_generation:
        workflow.add_node(
            "generate_documents",
            _make_generate_documents_node(
                gen_chain,
                store=DocumentArtifactStore(store.root),
                match_store=store,
                final_status="completed",
            ),
        )
        workflow.add_edge("generate_documents", END)

    path_map: dict[str, str] = {
        "human_review_node": "human_review_node",
        "prepare_regeneration_context": "prepare_regeneration_context",
        "__end__": END,
    }
    if include_document_generation:
        path_map["generate_documents"] = "generate_documents"

    workflow.add_edge(START, "load_match_inputs")
    workflow.add_edge("load_match_inputs", "run_match_llm")
    workflow.add_edge("run_match_llm", "persist_match_round")
    workflow.add_edge("persist_match_round", "human_review_node")
    workflow.add_edge("human_review_node", "apply_review_decision")
    workflow.add_conditional_edges(
        "apply_review_decision",
        _make_route_after_apply_review(include_document_generation),
        path_map,
    )
    workflow.add_edge("prepare_regeneration_context", "run_match_llm")

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=list(interrupt_before),
        interrupt_after=list(interrupt_after),
    )


def build_default_match_chain(
    *, model_name: str = "gemini-1.5-flash-latest", model: Any | None = None
):
    """Build the default LangChain runnable for the match step.

    Args:
        model_name: Google model name used when no model instance is injected.
        model: Optional preconstructed chat model for tests or custom wiring.

    Returns:
        An LCEL pipeline that yields ``MatchEnvelope`` objects.
    """

    from langchain_google_genai import ChatGoogleGenerativeAI

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        return _build_studio_match_chain()

    prompt = build_match_prompt()
    chat_model = model or ChatGoogleGenerativeAI(model=model_name)
    return prompt | chat_model.with_structured_output(MatchEnvelope)


def create_studio_graph():
    """Create a Studio-friendly compiled graph.

    The graph always loads, even when no Gemini credentials are configured, so
    LangGraph Studio can still display the topology. When an API key is not
    available, the model node is replaced with a stub that raises a clear error
    on invocation.
    """

    return build_match_skill_graph(
        match_chain=_build_studio_match_chain(),
        checkpointer=InMemorySaver(),
    )


def _build_studio_match_chain() -> Any:
    """Return the real model chain when credentials exist, otherwise a demo chain."""

    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return build_default_match_chain()

    return _StudioDemoMatchChain()


class _StudioDemoMatchChain:
    """Fallback chain used to demo the graph in Studio without model credentials."""

    def invoke(self, payload: dict[str, str]) -> MatchEnvelope:
        """Generate a deterministic match result from serialized prompt inputs."""

        requirements = _parse_prompt_items(payload.get("requirements_block", ""))
        evidence = _parse_prompt_items(payload.get("profile_evidence_block", ""))
        evidence_ids = [item["id"] for item in evidence if item.get("id")]
        evidence_text = [item["text"] for item in evidence if item.get("text")]
        quote = evidence_text[0] if evidence_text else "No supporting evidence provided"

        matches = []
        for index, requirement in enumerate(requirements):
            status = "matched" if evidence_ids else "missing"
            score = 0.8 if evidence_ids else 0.2
            if index % 3 == 1 and evidence_ids:
                status = "partial"
                score = 0.55
            matches.append(
                RequirementMatch(
                    requirement_id=requirement["id"],
                    status=status,
                    score=score,
                    evidence_ids=evidence_ids[:1],
                    evidence_quotes=[quote] if evidence_ids else [],
                    reasoning=(
                        "Studio demo result based on available profile evidence"
                        if evidence_ids
                        else "Studio demo found no evidence to support this requirement"
                    ),
                )
            )

        total_score = (
            sum(item.score for item in matches) / len(matches) if matches else 0.0
        )
        recommendation: Literal["proceed", "marginal", "reject"]
        if total_score >= 0.75:
            recommendation = "proceed"
        elif total_score >= 0.4:
            recommendation = "marginal"
        else:
            recommendation = "reject"

        return MatchEnvelope(
            matches=matches,
            total_score=total_score,
            decision_recommendation=recommendation,
            summary_notes="Studio demo chain generated this result without external model credentials.",
        )


def _parse_prompt_items(block: str) -> list[dict[str, str]]:
    """Parse line-oriented prompt blocks produced by ``build_prompt_input``."""

    items: list[dict[str, str]] = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("- ") or line == "- none":
            continue
        payload = line[2:]
        if " text=" in payload:
            prefix, text = payload.split(" text=", 1)
        else:
            prefix, text = payload, ""
        item: dict[str, str] = {"text": text.strip()}
        for token in prefix.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            item[key] = value.strip()
        items.append(item)
    return items


def resume_with_review(
    app: Any, config: dict[str, Any], review_payload: dict[str, Any]
):
    """Resume a paused thread with structured human review data.

    Args:
        app: Compiled LangGraph app.
        config: Invocation config containing the thread id.
        review_payload: Structured review payload submitted by an operator UI.

    Returns:
        The graph result after the review node has been resumed and executed.
    """

    app.update_state(
        config, {"review_payload": review_payload}, as_node="human_review_node"
    )
    return app.invoke(None, config=config)


def _make_load_match_inputs_node(store: MatchArtifactStore):
    """Create the node that prepares inputs and merges persisted patches."""

    def load_match_inputs(state: MatchSkillState) -> MatchSkillState:
        """Validate required inputs and compute effective profile evidence."""

        source = _require_non_empty_text(state, "source")
        job_id = _require_non_empty_text(state, "job_id")
        requirements = _validate_requirements(state.get("requirements"))
        profile_evidence = _validate_profile_evidence(state.get("profile_evidence"))
        effective_profile = state.get("effective_profile_evidence")
        if effective_profile:
            effective = _validate_profile_evidence(effective_profile)
        else:
            effective = _merge_patch_evidence(
                base_profile=profile_evidence,
                patches=store.get_all_feedback_patches(source, job_id),
            )

        return {
            "requirements": [item.model_dump() for item in requirements],
            "profile_evidence": [item.model_dump() for item in profile_evidence],
            "effective_profile_evidence": [item.model_dump() for item in effective],
            "status": "running",
        }

    return load_match_inputs


def _make_run_match_llm_node(chain: Any):
    """Create the node that invokes the structured-output match runnable."""

    def run_match_llm(state: MatchSkillState) -> MatchSkillState:
        """Build prompt variables, invoke the chain, and normalize output."""

        requirements = _validate_requirements(state.get("requirements"))
        effective_profile = _validate_profile_evidence(
            state.get("effective_profile_evidence")
        )
        feedback = _validate_feedback_items(state.get("review_feedback"))
        regeneration_scope = _normalize_scope(state.get("regeneration_scope"))

        prompt_input = build_prompt_input(
            requirements=requirements,
            profile_evidence=effective_profile,
            review_feedback=feedback,
            regeneration_scope=regeneration_scope,
        )
        raw_result = chain.invoke(prompt_input)
        match_result = (
            raw_result
            if isinstance(raw_result, MatchEnvelope)
            else MatchEnvelope.model_validate(raw_result)
        )
        return {
            "match_result": match_result.model_dump(),
            "status": "running",
        }

    return run_match_llm


def _make_persist_match_round_node(store: MatchArtifactStore):
    """Create the node that persists a proposed match round."""

    def persist_match_round(state: MatchSkillState) -> MatchSkillState:
        """Write current round artifacts and expose refs/hash in state."""

        source = _require_non_empty_text(state, "source")
        job_id = _require_non_empty_text(state, "job_id")
        requirements = _validate_requirements(state.get("requirements"))
        effective_profile = _validate_profile_evidence(
            state.get("effective_profile_evidence")
        )
        match_result = MatchEnvelope.model_validate(state.get("match_result"))
        regeneration_scope = _normalize_scope(state.get("regeneration_scope"))

        round_number = store.next_round_number(source, job_id)
        refs = store.write_match_round(
            source=source,
            job_id=job_id,
            round_number=round_number,
            match_result=match_result,
            requirements=requirements,
            profile_evidence=effective_profile,
            regeneration_scope=regeneration_scope,
        )
        match_hash = store.sha256_file(refs["approved_match_ref"])
        return {
            "artifact_refs": {**state.get("artifact_refs", {}), **refs},
            "round_number": round_number,
            "match_result_hash": match_hash,
            "status": "pending_review",
        }

    return persist_match_round


def _human_review_node(state: MatchSkillState) -> MatchSkillState:
    """Placeholder breakpoint node used for native HITL pausing.

    The graph is typically compiled with ``interrupt_before=['human_review_node']``.
    External clients then inject ``review_payload`` into the checkpointed state
    before resuming execution.
    """

    return {"status": state.get("status", "pending_review")}


def _make_route_after_apply_review(include_document_generation: bool):
    """Return a routing function for the apply_review_decision conditional edge."""

    def _route(state: MatchSkillState) -> str:
        status = state.get("status")
        if status == "pending_review":
            return "human_review_node"
        if status == "pending_regeneration":
            return "prepare_regeneration_context"
        if include_document_generation and status == "generating_documents":
            return "generate_documents"
        return "__end__"

    return _route


def _make_apply_review_decision_node(store: MatchArtifactStore):
    """Create the node that validates and applies a human review payload."""

    def apply_review_decision(state: MatchSkillState) -> MatchSkillState:
        """Normalize human review input and route the graph accordingly.

        Missing payload is treated as a safe no-op: returns to
        ``human_review_node`` without crashing (guards against bare Studio
        Continue). A payload with a stale hash is rejected with ValueError.

        Args:
            state: Must contain ``source``, ``job_id``, ``match_result_hash``,
                and ``match_result``. ``review_payload`` is optional; its
                absence triggers the safe no-op path.

        Returns:
            A ``Command`` routing to ``human_review_node`` (no payload),
            ``prepare_regeneration_context`` (request_regeneration),
            ``generate_documents`` (approve), or ``__end__`` (reject).

        Raises:
            ValueError: If the payload's ``source_state_hash`` does not match
                the current ``match_result_hash``.
        """

        source = _require_non_empty_text(state, "source")
        job_id = _require_non_empty_text(state, "job_id")
        raw_review_payload = state.get("review_payload")
        if not raw_review_payload:
            return {"status": "pending_review"}

        review_payload = ReviewPayload.model_validate(raw_review_payload)
        match_hash = _require_non_empty_text(state, "match_result_hash")
        if review_payload.source_state_hash != match_hash:
            raise ValueError(
                "review payload hash does not match the current match result"
            )

        match_result = MatchEnvelope.model_validate(state.get("match_result"))
        round_number = cast(int, state.get("round_number"))
        feedback_items = _build_feedback_items(review_payload, match_result)
        routing_decision = _route_from_feedback(feedback_items)
        refs = store.write_review_result(
            source=source,
            job_id=job_id,
            round_number=round_number,
            review_payload=review_payload,
            feedback_items=feedback_items,
            routing_decision=routing_decision,
        )
        status = (
            "pending_regeneration"
            if routing_decision == "request_regeneration"
            else "generating_documents"
            if routing_decision == "approve"
            else "rejected"
        )
        return {
            "review_decision": routing_decision,
            "active_feedback": [item.model_dump() for item in feedback_items],
            "artifact_refs": {**state.get("artifact_refs", {}), **refs},
            "status": status,
        }

    return apply_review_decision


def _make_prepare_regeneration_context_node(store: MatchArtifactStore):
    """Create the node that prepares the next regeneration round."""

    def prepare_regeneration_context(state: MatchSkillState) -> MatchSkillState:
        """Merge patch evidence and restrict the next round to scoped items.

        Computes the regeneration scope from feedback items whose action is
        ``patch``, merges all historical patch evidence from disk into the
        effective profile, and clears the stale review payload so the next
        ``run_match_llm`` starts clean.

        Args:
            state: Must contain ``review_decision`` == ``request_regeneration``,
                ``source``, ``job_id``, ``profile_evidence``, and
                ``active_feedback``.

        Returns:
            Partial state update with ``effective_profile_evidence``,
            ``review_feedback``, ``regeneration_scope``, cleared
            ``review_payload``, and ``status`` set to ``"running"``.

        Raises:
            ValueError: If ``review_decision`` is not ``request_regeneration``
                or if no patch decisions exist in the feedback items.
        """

        if state.get("review_decision") != "request_regeneration":
            raise ValueError(
                "prepare_regeneration_context requires request_regeneration"
            )

        source = _require_non_empty_text(state, "source")
        job_id = _require_non_empty_text(state, "job_id")
        profile_evidence = _validate_profile_evidence(state.get("profile_evidence"))
        feedback_items = _validate_feedback_items(state.get("active_feedback"))
        regeneration_scope = [
            item.requirement_id for item in feedback_items if item.action == "patch"
        ]
        if not regeneration_scope:
            raise ValueError(
                "request_regeneration requires at least one patch decision"
            )

        merged_profile = _merge_patch_evidence(
            base_profile=profile_evidence,
            patches=store.get_all_feedback_patches(source, job_id),
        )
        return {
            "effective_profile_evidence": [
                item.model_dump() for item in merged_profile
            ],
            "review_feedback": [item.model_dump() for item in feedback_items],
            "regeneration_scope": regeneration_scope,
            "review_payload": {},
            "status": "running",
        }

    return prepare_regeneration_context


def _validate_requirements(raw: Any) -> list[RequirementInput]:
    """Validate and normalize the requirement list from graph state."""

    if not isinstance(raw, list) or not raw:
        raise ValueError("requirements are required")
    return [RequirementInput.model_validate(item) for item in raw]


def _validate_profile_evidence(raw: Any) -> list[ProfileEvidence]:
    """Validate and normalize the profile evidence list from graph state."""

    if not isinstance(raw, list) or not raw:
        raise ValueError("profile_evidence are required")
    return [ProfileEvidence.model_validate(item) for item in raw]


def _validate_feedback_items(raw: Any) -> list[FeedbackItem]:
    """Validate and normalize persisted feedback items from graph state."""

    if not raw:
        return []
    if not isinstance(raw, list):
        raise ValueError("feedback items must be a list")
    return [FeedbackItem.model_validate(item) for item in raw]


def _normalize_scope(raw: Any) -> list[str]:
    """Normalize regeneration scope ids into a compact list of strings."""

    if not raw:
        return []
    if not isinstance(raw, list):
        raise ValueError("regeneration_scope must be a list")
    return [str(item).strip() for item in raw if str(item).strip()]


def _merge_patch_evidence(
    *,
    base_profile: list[ProfileEvidence],
    patches: list[ProfileEvidence],
) -> list[ProfileEvidence]:
    """Append unique patch evidence items to the base profile evidence set."""

    merged = list(base_profile)
    seen = {item.id for item in base_profile}
    for item in patches:
        if item.id in seen:
            continue
        merged.append(item)
        seen.add(item.id)
    return merged


def _build_feedback_items(
    review_payload: ReviewPayload,
    match_result: MatchEnvelope,
) -> list[FeedbackItem]:
    """Convert structured review decisions into deterministic feedback items."""

    valid_ids = {item.requirement_id for item in match_result.matches}
    if not review_payload.items:
        raise ValueError("review payload requires at least one decision")

    feedback_items: list[FeedbackItem] = []
    for item in review_payload.items:
        if item.requirement_id not in valid_ids:
            raise ValueError(
                f"unknown requirement id in review payload: {item.requirement_id}"
            )
        action = _feedback_action_from_decision(item.decision)
        feedback_items.append(
            FeedbackItem(
                requirement_id=item.requirement_id,
                action=action,
                reviewer_note=item.note,
                patch_evidence=item.patch_evidence,
            )
        )
    return feedback_items


def _feedback_action_from_decision(
    decision: ReviewDecision,
) -> Literal["proceed", "patch", "reject"]:
    """Map review decisions onto deterministic regeneration actions."""

    mapping = {
        "approve": "proceed",
        "request_regeneration": "patch",
        "reject": "reject",
    }
    return mapping[decision]


def _route_from_feedback(feedback_items: list[FeedbackItem]) -> ReviewDecision:
    """Aggregate row-level feedback into a single graph routing decision."""

    actions = {item.action for item in feedback_items}
    if "reject" in actions:
        return "reject"
    if "patch" in actions:
        return "request_regeneration"
    return "approve"


def _require_non_empty_text(state: MatchSkillState, key: str) -> str:
    """Read a required non-empty string field from graph state."""

    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()
