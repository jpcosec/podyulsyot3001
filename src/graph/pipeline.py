"""LangGraph coordinator for application pipeline run/resume flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from operator import add
from pathlib import Path
from typing import Annotated

from typing_extensions import Required, TypedDict

from src.steps import StepResult
from src.steps.cv_tailoring import run as run_tailor_cv
from src.steps.email_draft import run as run_email
from src.steps.ingestion import run as run_ingest
from src.steps.matching import approve as run_match_approve
from src.steps.matching import run as run_match
from src.steps.motivation import run as run_motivation
from src.steps.packaging import run as run_package
from src.steps.rendering import run as run_render
from src.utils.state import JobState


@dataclass
class GraphRunResult:
    """Outcome of a graph pipeline execution attempt."""

    status: str
    message: str
    step_results: list[tuple[str, StepResult]] = field(default_factory=list)
    interrupted_at: str | None = None


class PipelineGraphState(TypedDict, total=False):
    """Mutable state passed between LangGraph nodes."""

    job_id: Required[str]
    source: Required[str]
    force: bool
    via: str
    docx_template: str
    language: str
    message: str
    step_results: Annotated[list[dict], add]


def _serialize_step_result(step_name: str, result: StepResult) -> dict:
    return {
        "step_name": step_name,
        "status": result.status,
        "produced": result.produced,
        "comments_found": result.comments_found,
        "message": result.message,
    }


def _deserialize_step_results(items: list[dict] | None) -> list[tuple[str, StepResult]]:
    if not items:
        return []

    parsed: list[tuple[str, StepResult]] = []
    for item in items:
        parsed.append(
            (
                str(item.get("step_name", "unknown")),
                StepResult(
                    status=str(item.get("status", "error")),
                    produced=list(item.get("produced", [])),
                    comments_found=int(item.get("comments_found", 0)),
                    message=str(item.get("message", "")),
                ),
            )
        )
    return parsed


def _to_job_state(state: PipelineGraphState) -> JobState:
    job_id = state.get("job_id")
    if not job_id:
        raise ValueError("Missing required graph state key: job_id")
    return JobState(str(job_id), source=str(state.get("source", "tu_berlin")))


def _assert_ok(step_name: str, result: StepResult) -> dict:
    payload = {
        "step_results": [_serialize_step_result(step_name, result)],
        "message": result.message,
    }
    if result.status == "error":
        raise RuntimeError(result.message)
    return payload


def _ingest_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_ingest(job_state, force=bool(state.get("force", False)))
    return _assert_ok("ingest", result)


def _match_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_match(job_state, force=bool(state.get("force", False)))
    return _assert_ok("match", result)


def _review_gate_node(state: PipelineGraphState) -> dict:
    from langgraph.types import interrupt  # type: ignore[import-not-found]

    job_state = _to_job_state(state)
    reviewed_mapping_path = job_state.artifact_path("planning/reviewed_mapping.json")

    if reviewed_mapping_path.exists() and not bool(state.get("force", False)):
        return _assert_ok(
            "review_gate",
            StepResult(
                status="skipped",
                produced=[],
                comments_found=0,
                message=f"Review already locked for job {job_state.job_id}",
            ),
        )

    interrupt(
        {
            "proposal_path": str(job_state.artifact_path("planning/match_proposal.md")),
            "job_id": job_state.job_id,
        }
    )
    result = run_match_approve(job_state)
    return _assert_ok("review_gate", result)


def _motivate_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_motivation(job_state, force=bool(state.get("force", False)))
    return _assert_ok("motivate", result)


def _tailor_cv_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_tailor_cv(
        job_state,
        force=bool(state.get("force", False)),
        language=str(state.get("language", "english")),
    )
    return _assert_ok("tailor-cv", result)


def _email_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_email(job_state, force=bool(state.get("force", False)))
    return _assert_ok("draft-email", result)


def _render_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_render(
        job_state,
        force=bool(state.get("force", False)),
        via=str(state.get("via", "docx")),
        docx_template=str(state.get("docx_template", "modern")),
        language=str(state.get("language", "english")),
    )
    return _assert_ok("render", result)


def _package_node(state: PipelineGraphState) -> dict:
    job_state = _to_job_state(state)
    result = run_package(job_state, force=bool(state.get("force", False)))
    return _assert_ok("package", result)


def build_graph():
    """Build the LangGraph pipeline DAG for run/resume orchestration."""
    from langgraph.graph import END, START, StateGraph  # type: ignore[import-not-found]

    builder = StateGraph(PipelineGraphState)
    builder.add_node("ingest", _ingest_node)
    builder.add_node("match", _match_node)
    builder.add_node("review_gate", _review_gate_node)
    builder.add_node("motivate", _motivate_node)
    builder.add_node("tailor_cv", _tailor_cv_node)
    builder.add_node("email", _email_node)
    builder.add_node("render", _render_node)
    builder.add_node("package", _package_node)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "match")
    builder.add_edge("match", "review_gate")
    builder.add_edge("review_gate", "motivate")
    builder.add_edge("motivate", "tailor_cv")
    builder.add_edge("tailor_cv", "email")
    builder.add_edge("email", "render")
    builder.add_edge("render", "package")
    builder.add_edge("package", END)
    return builder


def _checkpoint_db_path(job_state: JobState) -> Path:
    db_dir = job_state.job_dir / ".graph"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "checkpoints.db"


def _read_checkpoint_results(graph, config: dict) -> list[tuple[str, StepResult]]:
    snapshot = graph.get_state(config)
    values = snapshot.values if snapshot else {}
    return _deserialize_step_results(values.get("step_results", []))


def run_graph_pipeline(
    state: JobState,
    *,
    force: bool = False,
    resume: bool = False,
    via: str = "docx",
    docx_template: str = "modern",
    language: str = "english",
) -> GraphRunResult:
    """Run or resume the LangGraph pipeline with SQLite checkpointing."""
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore[import-not-found]
        from langgraph.types import Command  # type: ignore[import-not-found]
    except ImportError as exc:
        return GraphRunResult(
            status="error",
            message=(
                "LangGraph runtime is unavailable. Install `langgraph` and "
                "`langgraph-checkpoint-sqlite` in the project environment."
            ),
        )

    db_path = _checkpoint_db_path(state)
    if not resume and db_path.exists():
        db_path.unlink()

    config = {"configurable": {"thread_id": f"{state.source}/{state.job_id}"}}
    initial_state: PipelineGraphState = {
        "job_id": state.job_id,
        "source": state.source,
        "force": force,
        "via": via,
        "docx_template": docx_template,
        "language": language,
        "step_results": [],
    }

    builder = build_graph()
    conn_string = f"sqlite:///{db_path}"
    with SqliteSaver.from_conn_string(conn_string) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)

        try:
            if resume:
                output = graph.invoke(Command(resume=True), config=config)
            else:
                output = graph.invoke(initial_state, config=config)
        except Exception as exc:
            return GraphRunResult(
                status="error",
                message=str(exc),
                step_results=_read_checkpoint_results(graph, config),
            )

        if isinstance(output, dict) and "__interrupt__" in output:
            return GraphRunResult(
                status="interrupted",
                message=(
                    "Review required: edit planning/match_proposal.md and rerun with --resume"
                ),
                step_results=_read_checkpoint_results(graph, config),
                interrupted_at="review_gate",
            )

        step_results = _deserialize_step_results(output.get("step_results", []))
        return GraphRunResult(
            status="ok",
            message=f"LangGraph pipeline complete for job {state.job_id}",
            step_results=step_results,
        )
