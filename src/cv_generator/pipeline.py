"""Multi-agent CV tailoring pipeline: MATCHER -> SELLER -> REALITY-CHECKER."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.cv_generator.config import CVConfig
from src.cv_generator.loaders.profile_loader import load_base_profile
from src.cv_generator.model import CVModel
from src.models.job import JobPosting, JobRequirement
from src.models.pipeline_contract import PipelineState
from src.prompts import load_prompt
from src.utils.gemini import GeminiClient

logger = logging.getLogger(__name__)


class CVTailoringPipeline:
    """Runs MATCHER -> SELLER -> REALITY-CHECKER to produce tailored CV claims."""

    AGENT_SECTIONS = {
        "matcher": "AGENT 1 — MATCHER",
        "seller": "AGENT 2 — SELLER",
        "checker": "AGENT 3 — REALITY-CHECKER",
    }

    def __init__(self, config: CVConfig | None = None):
        self.config = config or CVConfig.from_defaults()
        self.gemini = GeminiClient()
        self.full_prompt = load_prompt("cv_multi_agent")

    def _extract_agent_prompt(self, agent_key: str) -> str:
        """Extract a single agent prompt section from the full prompt file."""
        header = self.AGENT_SECTIONS.get(agent_key)
        if header is None:
            raise ValueError(f"Unknown agent key: {agent_key}")

        start = self.full_prompt.find(header)
        if start == -1:
            raise ValueError(f"Prompt section not found: {header}")

        next_headers = [
            self.full_prompt.find(section, start + 1)
            for section in self.AGENT_SECTIONS.values()
            if section != header
        ]
        next_headers.append(self.full_prompt.find("AGENT 4 — RENDERER", start + 1))
        end_candidates = [idx for idx in next_headers if idx != -1 and idx > start]
        end = min(end_candidates) if end_candidates else len(self.full_prompt)
        return self.full_prompt[start:end].strip()

    @staticmethod
    def _extract_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in Gemini response")
        return text[start : end + 1]

    @staticmethod
    def _parse_job_md(job_md_path: Path) -> JobPosting:
        content = job_md_path.read_text(encoding="utf-8")
        title = ""
        reference_number = ""

        for line in content.splitlines():
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            if line.lower().startswith("reference_number:") and not reference_number:
                reference_number = line.split(":", 1)[1].strip()

        requirements = [
            JobRequirement(id=f"R{index}", text=line[6:].strip(), priority="must")
            for index, line in enumerate(content.splitlines(), start=1)
            if line.startswith("- [ ]") and line[6:].strip()
        ]

        return JobPosting(
            title=title,
            reference_number=reference_number,
            deadline="",
            institution="",
            department="",
            location="",
            contact_name="",
            contact_email="",
            requirements=requirements,
            themes=[],
            raw_text=content,
        )

    def _load_job_posting(self, job_dir: Path) -> JobPosting:
        summary_path = job_dir / "summary.json"
        job_md_path = job_dir / "job.md"

        if summary_path.exists():
            summary_data: dict[str, Any] = json.loads(
                summary_path.read_text(encoding="utf-8")
            )
            posting = JobPosting.from_summary_json(summary_data)
            if posting.raw_text:
                return posting
            if job_md_path.exists():
                posting.raw_text = job_md_path.read_text(encoding="utf-8")
            return posting

        if job_md_path.exists():
            return self._parse_job_md(job_md_path)

        raise FileNotFoundError(
            f"Neither summary.json nor job.md found in {job_dir.as_posix()}"
        )

    def _build_initial_context(
        self, job: JobPosting, profile: dict, model: CVModel
    ) -> str:
        """Build the input data string for the MATCHER step."""
        context = {
            "job": job.model_dump(),
            "profile": profile,
            "candidate": {
                "name": model.full_name,
                "tagline": model.tagline,
                "summary": model.summary,
                "skills": model.skills,
                "experience": [vars(item) for item in model.experience],
                "education": [vars(item) for item in model.education],
                "publications": [vars(item) for item in model.publications],
                "languages": [vars(item) for item in model.languages],
            },
        }
        return json.dumps(context, indent=2, ensure_ascii=True)

    def run_step(self, agent_key: str, input_data: str) -> PipelineState:
        """Run one agent step, validate output as PipelineState."""
        prompt = self._extract_agent_prompt(agent_key)
        schema = PipelineState.model_json_schema()
        full_input = (
            f"SYSTEM INSTRUCTIONS:\n{prompt}\n\n"
            "OUTPUT FORMAT:\n"
            "Return JSON only, matching this schema exactly:\n"
            f"{json.dumps(schema, indent=2, ensure_ascii=True)}\n\n"
            f"INPUT DATA:\n{input_data}"
        )
        response = self.gemini.generate(full_input)
        return PipelineState.model_validate_json(self._extract_json_object(response))

    def execute(self, job_id: str, source: str = "tu_berlin") -> PipelineState:
        """Run MATCHER -> SELLER -> CHECKER and persist intermediates/summary."""
        job_dir = self.config.pipeline_root / source / job_id
        job_posting = self._load_job_posting(job_dir)
        profile = load_base_profile(self.config.profile_path())
        model = CVModel.from_profile(profile)

        context = self._build_initial_context(job_posting, profile, model)

        logger.info("Running MATCHER...")
        matcher_state = self.run_step("matcher", context)
        self._save_intermediate(job_dir, "01_matcher.json", matcher_state)

        logger.info("Running SELLER...")
        seller_state = self.run_step("seller", matcher_state.model_dump_json(indent=2))
        self._save_intermediate(job_dir, "02_seller.json", seller_state)

        logger.info("Running REALITY-CHECKER...")
        final_state = self.run_step("checker", seller_state.model_dump_json(indent=2))
        self._save_intermediate(job_dir, "03_reality_checker.json", final_state)

        self._write_tailoring_md(job_dir, final_state)
        return final_state

    def _save_intermediate(self, job_dir: Path, filename: str, state: PipelineState):
        """Save pipeline intermediate to cv/pipeline_intermediates/."""
        out_dir = job_dir / "cv" / "pipeline_intermediates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / filename).write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _write_tailoring_md(self, job_dir: Path, state: PipelineState):
        """Write planning/cv_tailoring.md from approved claims."""
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
