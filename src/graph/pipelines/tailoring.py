"""CV tailoring pipeline built on top of shared agent runner."""

from __future__ import annotations

import logging
from pathlib import Path

from src.graph.agents.base import AgentRunner
from src.models.pipeline_contract import PipelineState
from src.utils.loaders.profile_loader import load_base_profile
from src.utils.model import CVModel

logger = logging.getLogger(__name__)


class CVTailoringPipeline(AgentRunner):
    """Runs MATCHER -> SELLER -> REALITY-CHECKER to produce tailored CV claims."""

    def execute(self, job_id: str, source: str = "tu_berlin") -> PipelineState:
        """Run MATCHER -> SELLER -> CHECKER and persist intermediates/summary."""
        job_dir = self.config.pipeline_root / source / job_id
        job_posting = self.load_job_posting(job_dir)
        profile = load_base_profile(self.config.profile_path())
        model = CVModel.from_profile(profile)

        context = self.build_initial_context(job_posting, profile, model)

        logger.info("Running MATCHER...")
        matcher_state = self.call_agent("matcher", context)
        self._save_intermediate(job_dir, "01_matcher.json", matcher_state)

        logger.info("Running SELLER...")
        seller_response = self.gemini.generate(
            self.build_step_input("seller", matcher_state.model_dump_json(indent=2))
        )
        seller_state = self.parse_response(
            seller_response,
            fallback_state=matcher_state,
        )
        self._save_intermediate(job_dir, "02_seller.json", seller_state)

        logger.info("Running REALITY-CHECKER...")
        checker_response = self.gemini.generate(
            self.build_step_input("checker", seller_state.model_dump_json(indent=2))
        )
        final_state = self.parse_response(
            checker_response,
            fallback_state=seller_state,
        )
        self._save_intermediate(job_dir, "03_reality_checker.json", final_state)

        self._write_tailoring_md(job_dir, final_state)
        return final_state

    @staticmethod
    def _save_intermediate(job_dir: Path, filename: str, state: PipelineState) -> None:
        out_dir = job_dir / "cv" / "pipeline_intermediates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / filename).write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _write_tailoring_md(job_dir: Path, state: PipelineState) -> None:
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        approved_claims = [
            claim for claim in state.proposed_claims if claim.status == "approved"
        ]

        lines = [
            "# CV Tailoring Brief",
            "",
            f"- Job: {state.job.title}",
            f"- Reference: {state.job.reference_number}",
            f"- Approved claims: {len(approved_claims)}",
            "",
            "## Approved Claims",
            "",
        ]

        if not approved_claims:
            lines.append("- No approved claims produced.")
        else:
            for claim in approved_claims:
                subsection = (
                    f" ({claim.target_subsection})" if claim.target_subsection else ""
                )
                lines.append(
                    f"- [{claim.target_section}{subsection}] {claim.claim_text}"
                )

        (planning_dir / "cv_tailoring.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )


CVMultiAgentPipeline = CVTailoringPipeline
