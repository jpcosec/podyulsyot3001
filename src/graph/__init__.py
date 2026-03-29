"""Graph orchestration layer for the unified pipeline.

This module wires together the scraper, translator, match skill, document
generator, render, and packaging modules into a single LangGraph pipeline.

Pipeline flow:
    scrape → translate → extract_bridge → match_skill → generate_documents → render → package
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph

from src.ai.match_skill.contracts import (
    MatchEnvelope,
    ProfileEvidence,
    RequirementInput,
)

logger = logging.getLogger(__name__)

RunStatus = Literal["pending", "running", "paused", "completed", "failed"]


class ErrorContext(TypedDict):
    """Error information propagated through the graph."""

    node: str
    message: str
    details: dict[str, Any] | None


class GraphState(TypedDict, total=False):
    """Unified state carried through the top-level pipeline graph.

    Identity:
        - source: Job portal source identifier
        - job_id: Unique job posting identifier
        - run_id: Unique run identifier for this pipeline execution

    Routing:
        - current_node: Name of the node most recently executed
        - status: Current execution status

    Summary payloads (for Studio inspection):
        - requirements: List of requirement inputs for match skill
        - profile_evidence: List of profile evidence for matching
        - match_result: Match envelope from match skill

    Artifact refs (full data on disk):
        - artifact_refs: Dictionary mapping artifact names to file paths

    Error tracking:
        - error_state: Error context if a node failed
    """

    source: str
    job_id: str
    run_id: str
    current_node: str
    status: RunStatus
    requirements: list[RequirementInput]
    profile_evidence: list[ProfileEvidence]
    match_result: MatchEnvelope | None
    artifact_refs: dict[str, str]
    error_state: ErrorContext | None


async def scrape_node(state: GraphState) -> dict:
    """Scrape job postings from the specified source.

    Calls the SmartScraperAdapter directly, not the CLI main.py.
    """
    from src.ai.scraper.main import PROVIDERS
    from src.ai.scraper.smart_adapter import SmartScraperAdapter

    source = state["source"]
    job_id = state.get("job_id")

    try:
        adapter: SmartScraperAdapter = PROVIDERS[source]
        already_scraped = []

        if job_id:
            data_path = Path(f"data/source/{source}")
            if data_path.exists():
                already_scraped = [
                    d for d in data_path.iterdir() if d.is_dir() and d.name == job_id
                ]
                already_scraped = [d.name for d in already_scraped]

        result = await adapter.run(
            already_scraped=already_scraped,
            limit=1 if job_id else None,
        )

        return {
            "artifact_refs": {
                "scrape_state": f"data/source/{source}/{job_id}/extracted_data.json"
                if job_id
                else f"data/source/{source}/",
                "scrape_content": f"data/source/{source}/{job_id}/content.md"
                if job_id
                else "",
            },
            "current_node": "scrape",
            "status": "running",
        }
    except Exception as e:
        logger.error(f"Scrape node failed: {e}")
        return {
            "current_node": "scrape",
            "status": "failed",
            "error_state": {"node": "scrape", "message": str(e), "details": None},
        }


async def translate_node(state: GraphState) -> dict:
    """Translate scraped job posting to English.

    Calls the translator adapter directly.
    """
    from src.tools.translator.providers.google.adapter import GoogleTranslatorAdapter
    from src.tools.translator.main import P_FIELDS_TO_TRANSLATE

    source = state["source"]
    job_id = state["job_id"]

    try:
        adapter = GoogleTranslatorAdapter()
        source_path = Path(f"data/source/{source}/{job_id}")

        json_path = source_path / "extracted_data.json"
        md_path = source_path / "content.md"

        if not json_path.exists() or not md_path.exists():
            raise FileNotFoundError(f"Missing scraped files for {source}/{job_id}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        orig_lang = data.get("original_language", "auto")

        if orig_lang == "en":
            return {
                "artifact_refs": {
                    **state.get("artifact_refs", {}),
                    "translated_state": str(json_path),
                    "translated_content": str(md_path),
                },
                "current_node": "translate",
                "status": "running",
            }

        translated_data = adapter.translate_fields(
            data, fields=P_FIELDS_TO_TRANSLATE, target_lang="en", source_lang=orig_lang
        )
        translated_data["original_language"] = "en"

        md_content = md_path.read_text(encoding="utf-8")
        translated_md = adapter.translate_text(
            md_content, target_lang="en", source_lang=orig_lang
        )

        out_json = source_path / "extracted_data_en.json"
        out_md = source_path / "content_en.md"

        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)

        out_md.write_text(translated_md, encoding="utf-8")

        return {
            "artifact_refs": {
                **state.get("artifact_refs", {}),
                "translated_state": str(out_json),
                "translated_content": str(out_md),
            },
            "current_node": "translate",
            "status": "running",
        }
    except Exception as e:
        logger.error(f"Translate node failed: {e}")
        return {
            "current_node": "translate",
            "status": "failed",
            "error_state": {
                "node": "translate",
                "message": str(e),
                "details": None,
            },
        }


async def extract_bridge_node(state: GraphState) -> dict:
    """Transform scraper output to match_skill input format."""
    from src.graph.nodes.extract_bridge import extract_bridge as run_extract_bridge

    source = state["source"]
    job_id = state["job_id"]

    try:
        requirements = run_extract_bridge(source=source, job_id=job_id)

        output_path = (
            Path("output/match_skill")
            / source
            / job_id
            / "nodes"
            / "extract_bridge"
            / "proposed"
            / "state.json"
        )

        return {
            "requirements": requirements,
            "artifact_refs": {
                **state.get("artifact_refs", {}),
                "bridge_state": str(output_path),
            },
            "current_node": "extract_bridge",
            "status": "running",
        }
    except Exception as e:
        logger.error(f"Extract bridge node failed: {e}")
        return {
            "current_node": "extract_bridge",
            "status": "failed",
            "error_state": {
                "node": "extract_bridge",
                "message": str(e),
                "details": None,
            },
        }


def _make_match_skill_subgraph():
    """Build the match skill subgraph with checkpointing."""
    from src.ai.match_skill.graph import build_match_skill_graph

    checkpointer = InMemorySaver()
    return build_match_skill_graph(checkpointer=checkpointer)


async def match_skill_node(state: GraphState) -> dict:
    """Execute the match skill subgraph.

    This node runs the full match skill graph (including HITL review loop)
    as a subgraph of the pipeline.
    """
    from src.ai.match_skill.graph import build_match_skill_graph

    source = state["source"]
    job_id = state["job_id"]
    requirements = state.get("requirements", [])
    profile_evidence = state.get("profile_evidence", [])

    if not requirements:
        return {
            "current_node": "match_skill",
            "status": "failed",
            "error_state": {
                "node": "match_skill",
                "message": "No requirements available for matching",
                "details": None,
            },
        }

    if not profile_evidence:
        profile_evidence = _load_profile_evidence()

    try:
        checkpointer = InMemorySaver()
        app = build_match_skill_graph(checkpointer=checkpointer)

        thread_id = f"{source}-{job_id}-{state.get('run_id', 'default')}"

        initial_state = {
            "source": source,
            "job_id": job_id,
            "requirements": [req.model_dump() for req in requirements],
            "profile_evidence": [ev.model_dump() for ev in profile_evidence],
            "artifact_refs": state.get("artifact_refs", {}),
        }

        result = app.invoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}},
        )

        return {
            "match_result": result.get("match_result"),
            "artifact_refs": {
                **state.get("artifact_refs", {}),
                **result.get("artifact_refs", {}),
            },
            "current_node": "match_skill",
            "status": "completed" if result.get("status") == "completed" else "running",
        }
    except Exception as e:
        logger.error(f"Match skill node failed: {e}")
        return {
            "current_node": "match_skill",
            "status": "failed",
            "error_state": {"node": "match_skill", "message": str(e), "details": None},
        }


async def generate_documents_node(state: GraphState) -> dict:
    """Generate CV and motivation letter documents."""
    from src.ai.generate_documents.graph import (
        build_default_generate_documents_chain,
    )
    from src.ai.generate_documents.storage import DocumentArtifactStore

    source = state["source"]
    job_id = state["job_id"]
    match_result = state.get("match_result")

    if not match_result:
        return {
            "current_node": "generate_documents",
            "status": "failed",
            "error_state": {
                "node": "generate_documents",
                "message": "No match result available for document generation",
                "details": None,
            },
        }

    try:
        store = DocumentArtifactStore()
        profile_data = _load_profile_data()
        chain = build_default_generate_documents_chain()

        input_payload = {
            "match_result": match_result.model_dump()
            if hasattr(match_result, "model_dump")
            else match_result,
            "profile_data": profile_data,
        }

        generated = chain.invoke(input_payload)

        doc_refs = store.write_documents(
            source=source,
            job_id=job_id,
            documents=generated.model_dump()
            if hasattr(generated, "model_dump")
            else generated,
        )

        return {
            "artifact_refs": {
                **state.get("artifact_refs", {}),
                **doc_refs,
            },
            "current_node": "generate_documents",
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Generate documents node failed: {e}")
        return {
            "current_node": "generate_documents",
            "status": "failed",
            "error_state": {
                "node": "generate_documents",
                "message": str(e),
                "details": None,
            },
        }


async def render_node(state: GraphState) -> dict:
    """Render generated documents to PDF/DOCX."""
    from src.tools.render.coordinator import RenderCoordinator
    from src.tools.render.request import RenderRequest

    source = state["source"]
    job_id = state["job_id"]

    try:
        coordinator = RenderCoordinator()
        artifact_refs = state.get("artifact_refs", {})

        cv_source = artifact_refs.get("cv_document")
        letter_source = artifact_refs.get("letter_document")

        rendered_refs = {}

        if cv_source:
            cv_request = RenderRequest(
                document_type="cv",
                engine="tex",
                language="en",
                source=cv_source,
                source_kind="direct",
            )
            cv_output = coordinator.render(cv_request)
            rendered_refs["rendered_cv"] = str(cv_output)

        if letter_source:
            letter_request = RenderRequest(
                document_type="letter",
                engine="tex",
                language="en",
                source=letter_source,
                source_kind="direct",
            )
            letter_output = coordinator.render(letter_request)
            rendered_refs["rendered_letter"] = str(letter_output)

        return {
            "artifact_refs": {
                **artifact_refs,
                **rendered_refs,
            },
            "current_node": "render",
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Render node failed: {e}")
        return {
            "current_node": "render",
            "status": "failed",
            "error_state": {"node": "render", "message": str(e), "details": None},
        }


async def package_node(state: GraphState) -> dict:
    """Package all artifacts into a final output directory."""
    import shutil

    source = state["source"]
    job_id = state["job_id"]
    artifact_refs = state.get("artifact_refs", {})

    try:
        output_dir = Path(f"output/{source}/{job_id}/nodes/package/final")
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "source": source,
            "job_id": job_id,
            "run_id": state.get("run_id"),
            "artifacts": {},
        }

        for name, ref_path in artifact_refs.items():
            if ref_path and Path(ref_path).exists():
                dest = output_dir / Path(ref_path).name
                if Path(ref_path).is_file():
                    shutil.copy2(ref_path, dest)
                manifest["artifacts"][name] = str(dest)

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        return {
            "artifact_refs": {
                **artifact_refs,
                "package_manifest": str(manifest_path),
            },
            "current_node": "package",
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Package node failed: {e}")
        return {
            "current_node": "package",
            "status": "failed",
            "error_state": {"node": "package", "message": str(e), "details": None},
        }


def _load_profile_evidence() -> list[ProfileEvidence]:
    """Load profile evidence from the default path or environment."""
    path = os.getenv(
        "PROFILE_EVIDENCE_PATH",
        "data/reference_data/profile/base_profile/profile_base_data.json",
    )

    try:
        if Path(path).exists():
            with open(path) as f:
                data = json.load(f)
            return [ProfileEvidence(**item) for item in data.get("evidence", [])]
    except Exception as e:
        logger.warning(f"Failed to load profile evidence: {e}")

    return [
        ProfileEvidence(
            id="DEFAULT_001",
            description="Default profile evidence for testing",
        )
    ]


def _load_profile_data() -> dict[str, Any]:
    """Load full profile data for document generation."""
    path = os.getenv(
        "PROFILE_DATA_PATH",
        "data/reference_data/profile/base_profile/profile_base_data.json",
    )

    try:
        if Path(path).exists():
            with open(path) as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load profile data: {e}")

    return {}


def build_pipeline_graph() -> Any:
    """Build the top-level pipeline graph.

    Returns:
        A compiled LangGraph app ready for invocation.
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("scrape", scrape_node)
    workflow.add_node("translate", translate_node)
    workflow.add_node("extract_bridge", extract_bridge_node)
    workflow.add_node("match_skill", match_skill_node)
    workflow.add_node("generate_documents", generate_documents_node)
    workflow.add_node("render", render_node)
    workflow.add_node("package", package_node)

    workflow.add_edge(START, "scrape")
    workflow.add_edge("scrape", "translate")
    workflow.add_edge("translate", "extract_bridge")
    workflow.add_edge("extract_bridge", "match_skill")
    workflow.add_edge("match_skill", "generate_documents")
    workflow.add_edge("generate_documents", "render")
    workflow.add_edge("render", "package")
    workflow.add_edge("package", "__end__")

    return workflow.compile(
        checkpointer=InMemorySaver(),
        interrupt_before=["match_skill"],
    )


def create_studio_graph() -> Any:
    """Create a Studio-friendly version of the pipeline graph.

    This version uses the InMemorySaver and is suitable for
    LangGraph Studio visualization.
    """
    return build_pipeline_graph()
