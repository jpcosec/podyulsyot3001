"""Shared infrastructure for matcher/seller/checker agent calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.job import JobPosting, JobRequirement
from src.models.pipeline_contract import PipelineState
from src.prompts import load_prompt
from src.utils.config import CVConfig
from src.utils.gemini import GeminiClient
from src.utils.model import CVModel


class AgentRunner:
    """Shared logic for running agent-based pipeline steps."""

    AGENT_SECTIONS = {
        "matcher": "AGENT 1 — MATCHER",
        "seller": "AGENT 2 — SELLER",
        "checker": "AGENT 3 — REALITY-CHECKER",
    }

    def __init__(self, config: CVConfig | None = None):
        self.config = config or CVConfig.from_defaults()
        self._gemini: GeminiClient | None = None
        self.full_prompt = load_prompt("cv_multi_agent")

    @property
    def gemini(self) -> GeminiClient:
        if self._gemini is None:
            self._gemini = GeminiClient()
        return self._gemini

    def extract_agent_prompt(self, agent_key: str) -> str:
        """Extract a single agent section from the full prompt."""
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
    def extract_json_object(text: str) -> str:
        """Return the first JSON object-like segment from model output."""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in Gemini response")
        return text[start : end + 1]

    @staticmethod
    def parse_job_md(job_md_path: Path) -> JobPosting:
        """Parse a minimal JobPosting from job.md fallback content."""
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

    def load_job_posting(self, job_dir: Path) -> JobPosting:
        """Load job posting from summary.json with job.md fallback."""
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
            return self.parse_job_md(job_md_path)

        raise FileNotFoundError(
            f"Neither summary.json nor job.md found in {job_dir.as_posix()}"
        )

    def build_initial_context(
        self, job: JobPosting, profile: dict, model: CVModel
    ) -> str:
        """Build initial JSON context for the matcher agent."""
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
            "full_job_description": job.raw_text,
        }
        return json.dumps(context, indent=2, ensure_ascii=True)

    def build_step_input(self, agent_key: str, input_data: str) -> str:
        """Build full system prompt + schema + input payload."""
        prompt = self.extract_agent_prompt(agent_key)
        schema = PipelineState.model_json_schema()
        return (
            f"SYSTEM INSTRUCTIONS:\n{prompt}\n\n"
            "OUTPUT FORMAT:\n"
            "Return JSON only, matching this schema exactly:\n"
            f"{json.dumps(schema, indent=2, ensure_ascii=True)}\n\n"
            f"INPUT DATA:\n{input_data}"
        )

    def parse_response(
        self,
        response: str,
        fallback_state: PipelineState | None = None,
    ) -> PipelineState:
        """Parse and normalize agent response into PipelineState."""
        payload: dict[str, Any] = json.loads(self.extract_json_object(response))

        if "evidence_items" not in payload and isinstance(payload.get("profile"), dict):
            profile_obj = payload["profile"]
            if isinstance(profile_obj.get("evidence_items"), list):
                payload["evidence_items"] = profile_obj.get("evidence_items", [])

        if fallback_state is not None:
            if "job" not in payload:
                payload["job"] = fallback_state.job.model_dump()
            if "evidence_items" not in payload:
                payload["evidence_items"] = [
                    item.model_dump() for item in fallback_state.evidence_items
                ]
            if "mapping" not in payload:
                payload["mapping"] = [
                    item.model_dump() for item in fallback_state.mapping
                ]
            if "render" not in payload:
                payload["render"] = fallback_state.render.model_dump()

        mapping_items = payload.get("mapping", [])
        if isinstance(mapping_items, list):
            normalized_mapping: list[dict[str, Any]] = []
            for item in mapping_items:
                if not isinstance(item, dict):
                    continue
                entry = dict(item)
                if "req_id" not in entry and "id" in entry:
                    entry["req_id"] = entry["id"]
                entry.setdefault("priority", "must")
                entry.setdefault("coverage", "none")
                entry.setdefault("evidence_ids", [])
                entry.setdefault("notes", "")
                normalized_mapping.append(entry)
            payload["mapping"] = normalized_mapping

        evidence_items = payload.get("evidence_items", [])
        if isinstance(evidence_items, list):
            valid_types = {
                "cv_line",
                "role",
                "project",
                "publication",
                "education",
                "skill",
                "language",
            }
            alias_types = {
                "summary": "cv_line",
                "experience": "role",
                "skills": "skill",
                "languages": "language",
                "cv": "cv_line",
                "bullet": "cv_line",
            }
            normalized_evidence: list[dict[str, Any]] = []
            for index, item in enumerate(evidence_items, start=1):
                if not isinstance(item, dict):
                    continue
                entry = dict(item)
                raw_type = str(entry.get("type", "cv_line")).strip().lower()
                mapped_type = alias_types.get(raw_type, raw_type)
                if mapped_type not in valid_types:
                    mapped_type = "cv_line"
                entry["type"] = mapped_type
                entry.setdefault("id", f"E{index}")
                entry.setdefault("text", "")
                entry.setdefault("source_ref", "")
                normalized_evidence.append(entry)
            payload["evidence_items"] = normalized_evidence

        return PipelineState.model_validate(payload)

    def call_agent(self, agent_key: str, input_data: str) -> PipelineState:
        """Run one agent and return normalized PipelineState."""
        response = self.gemini.generate(self.build_step_input(agent_key, input_data))
        return self.parse_response(response)
