"""Application orchestrator — tool-driven flow controller.

The orchestrator manages the high-level flow:
1. Scrape job URLs -> JobPosting models
2. Analyze fit for each job -> FitAnalysis
3. Rank and filter jobs -> ApplicationBatch (human approves)
4. For each approved job:
   a. Tailor CV (multi-agent pipeline) -> human reviews tailoring
   b. Render CV -> PDF
   c. Plan motivation letter -> human reviews plan
   d. Write motivation letter -> PDF
   e. Generate email draft
   f. Validate ATS
   g. Merge final PDF package
"""

import json
import logging
from pathlib import Path

from src.agent import tools
from src.utils.config import CVConfig
from src.models.application import ApplicationBatch, ApplicationPlan, FitAnalysis
from src.models.job import JobPosting

logger = logging.getLogger(__name__)


class ApplicationAgent:
    """Orchestrates the application process for a batch of job URLs."""

    def __init__(self, config: CVConfig | None = None):
        self.config = config or CVConfig.from_defaults()

    def plan(self, urls: list[str]) -> ApplicationBatch:
        """Phase 1: Scrape, analyze, rank, produce application plans.

        This phase is fully automated. Returns an ApplicationBatch
        for human review before proceeding to execution.
        """
        # 1. Scrape all URLs
        logger.info(f"Scraping {len(urls)} job URLs...")
        jobs = tools.scrape_jobs_batch(urls, config=self.config)
        logger.info(f"Scraped {len(jobs)} jobs successfully.")

        # 2. Analyze fit for each
        logger.info("Analyzing fit...")
        ranked = tools.rank_jobs(jobs, profile_path=self.config.profile_path())

        # 3. Build application plans
        plans = []
        skipped = []
        for i, (job, fit) in enumerate(ranked):
            if fit.recommendation == "skip":
                skipped.append(
                    {
                        "job": job.model_dump(),
                        "reason": fit.alignment_summary,
                        "score": fit.overall_score,
                    }
                )
                continue
            plans.append(
                ApplicationPlan(
                    job=job,
                    fit=fit,
                    cv_strategy=fit.alignment_summary,
                    motivation_strategy="",  # Filled during execution
                    priority=i + 1,
                )
            )

        batch = ApplicationBatch(plans=plans, skipped=skipped)
        self._write_batch_report(batch)
        return batch

    def execute_plan(
        self,
        plan: ApplicationPlan,
        source: str = "tu_berlin",
        via: str = "docx",
        docx_template: str = "modern",
    ) -> dict:
        """Phase 2: Execute a single application plan.

        Runs the full pipeline for one job:
        tailor -> render -> motivate -> email -> validate -> package.

        Returns a summary dict with paths to all generated artifacts.
        """
        job = plan.job
        job_id = (job.reference_number or "manual").replace("/", "-")

        results = {"job_id": job_id, "job_title": job.title}

        # 1. Tailor CV
        logger.info(f"Tailoring CV for {job_id}...")
        from src.models.pipeline_contract import PipelineState

        tailoring_state = tools.tailor_cv(
            job=job,
            pipeline_state=PipelineState(job=job, evidence_items=[], mapping=[]),
            config=self.config,
        )
        results["tailoring"] = (
            f"{len([c for c in tailoring_state.proposed_claims if c.status == 'approved'])} claims approved"
        )

        # 2. Render CV
        logger.info(f"Rendering CV for {job_id}...")
        cv_path = tools.render_cv(
            job_id=job_id,
            source=source,
            template=docx_template,
            via=via,
            config=self.config,
        )
        results["cv_pdf"] = str(cv_path)

        # 3. Plan motivation letter
        logger.info(f"Planning motivation letter for {job_id}...")
        letter_plan = tools.plan_motivation_letter(
            job_id=job_id, source=source, config=self.config
        )
        results["letter_plan_gaps"] = len(letter_plan.get("gaps", []))

        # 4. Write motivation letter
        logger.info(f"Writing motivation letter for {job_id}...")
        letter = tools.write_motivation_letter(
            job_id=job_id, source=source, config=self.config
        )
        results["letter_subject"] = letter.subject

        # 5. Build motivation PDF
        logger.info(f"Building motivation PDF for {job_id}...")
        letter_pdf = tools.build_motivation_pdf(
            job_id=job_id, source=source, config=self.config
        )
        results["letter_pdf"] = str(letter_pdf)

        # 6. Generate email draft
        logger.info(f"Generating email draft for {job_id}...")
        email = tools.generate_email_draft(
            job_id=job_id, source=source, config=self.config
        )
        results["email_subject"] = email.subject

        # 7. Validate ATS
        logger.info(f"Running ATS validation for {job_id}...")
        ats_report = tools.score_ats(
            job_id=job_id,
            source=source,
            ats_target="pdf",
            config=self.config,
        )
        results["ats_score"] = ats_report.get("score", 0)

        return results

    def _write_batch_report(self, batch: ApplicationBatch):
        """Write the batch analysis report for human review."""
        report_path = self.config.pipeline_root / "batch_report.md"
        lines = ["# Application Batch Report", ""]

        for plan in batch.plans:
            lines.append(f"## [{plan.priority}] {plan.job.title}")
            lines.append(f"- **Reference:** {plan.job.reference_number}")
            lines.append(f"- **Score:** {plan.fit.overall_score}/100")
            lines.append(f"- **Eligibility:** {plan.fit.eligibility}")
            lines.append(f"- **Recommendation:** {plan.fit.recommendation}")
            lines.append(f"- **Strategy:** {plan.cv_strategy}")
            if plan.fit.gaps:
                lines.append(f"- **Gaps:** {', '.join(plan.fit.gaps)}")
            lines.append("")

        if batch.skipped:
            lines.append("## Skipped Jobs")
            for s in batch.skipped:
                lines.append(
                    f"- {s.get('job', {}).get('title', '?')} (score: {s.get('score', '?')}): {s.get('reason', '')}"
                )

        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Batch report written to {report_path}")
