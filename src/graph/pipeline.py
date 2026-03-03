"""Graph-oriented coordinator for the job application pipeline.

This module provides a migration-safe orchestration entrypoint for
`pipeline job <id> run` with interrupt/resume behavior at the review gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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


class GraphPipelineRunner:
    """Coordinates step modules as a graph-style run with review interrupt."""

    def __init__(self, state: JobState):
        self.state = state
        self._results: list[tuple[str, StepResult]] = []

    def _execute(self, step_name: str, result: StepResult) -> GraphRunResult | None:
        self._results.append((step_name, result))
        if result.status == "error":
            return GraphRunResult(
                status="error",
                message=result.message,
                step_results=self._results,
            )
        return None

    def run(
        self,
        *,
        force: bool = False,
        resume: bool = False,
        via: str = "docx",
        docx_template: str = "modern",
        language: str = "english",
    ) -> GraphRunResult:
        """Run from current state until completion or review interrupt."""
        if force or not self.state.step_complete("ingestion"):
            failure = self._execute("ingest", run_ingest(self.state, force=force))
            if failure:
                return failure

        has_proposal = self.state.artifact_path("planning/match_proposal.md").exists()
        has_keywords = self.state.artifact_path("planning/keywords.json").exists()
        if force or not (has_proposal and has_keywords):
            failure = self._execute("match", run_match(self.state, force=force))
            if failure:
                return failure

        reviewed_mapping_path = self.state.artifact_path(
            "planning/reviewed_mapping.json"
        )
        if force and reviewed_mapping_path.exists():
            reviewed_mapping_path.unlink()

        if not reviewed_mapping_path.exists():
            if not resume:
                return GraphRunResult(
                    status="interrupted",
                    message=(
                        "Review required: edit planning/match_proposal.md and rerun with --resume"
                    ),
                    step_results=self._results,
                    interrupted_at="review_gate",
                )

            failure = self._execute("review", run_match_approve(self.state))
            if failure:
                return failure

        if force or not self.state.step_complete("motivation"):
            failure = self._execute("motivate", run_motivation(self.state, force=force))
            if failure:
                return failure

        if force or not self.state.step_complete("cv_tailoring"):
            failure = self._execute(
                "tailor-cv",
                run_tailor_cv(self.state, force=force, language=language),
            )
            if failure:
                return failure

        if force or not self.state.step_complete("email_draft"):
            failure = self._execute("draft-email", run_email(self.state, force=force))
            if failure:
                return failure

        if force or not self.state.step_complete("rendering"):
            failure = self._execute(
                "render",
                run_render(
                    self.state,
                    force=force,
                    via=via,
                    docx_template=docx_template,
                    language=language,
                ),
            )
            if failure:
                return failure

        if force or not self.state.step_complete("packaging"):
            failure = self._execute("package", run_package(self.state, force=force))
            if failure:
                return failure

        return GraphRunResult(
            status="ok",
            message=f"Graph pipeline complete for job {self.state.job_id}",
            step_results=self._results,
        )


def run_graph_pipeline(
    state: JobState,
    *,
    force: bool = False,
    resume: bool = False,
    via: str = "docx",
    docx_template: str = "modern",
    language: str = "english",
) -> GraphRunResult:
    """Convenience wrapper for graph-style pipeline execution."""
    runner = GraphPipelineRunner(state)
    return runner.run(
        force=force,
        resume=resume,
        via=via,
        docx_template=docx_template,
        language=language,
    )
