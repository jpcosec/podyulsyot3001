"""Multi-agent CV tailoring pipeline: MATCHER -> SELLER -> REALITY-CHECKER."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.cv_generator.config import CVConfig
from src.cv_generator.loaders.profile_loader import load_base_profile
from src.cv_generator.model import CVModel
from src.models.job import JobPosting, JobRequirement
from src.models.pipeline_contract import PipelineState, ReviewedClaim, ReviewedMapping
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
            "full_job_description": job.raw_text,
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
        return self._parse_pipeline_state_response(response)

    def _parse_pipeline_state_response(
        self,
        response: str,
        fallback_state: PipelineState | None = None,
    ) -> PipelineState:
        payload: dict[str, Any] = json.loads(self._extract_json_object(response))

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
        seller_response = self.gemini.generate(
            self._build_step_input("seller", matcher_state.model_dump_json(indent=2))
        )
        seller_state = self._parse_pipeline_state_response(
            seller_response,
            fallback_state=matcher_state,
        )
        self._save_intermediate(job_dir, "02_seller.json", seller_state)

        logger.info("Running REALITY-CHECKER...")
        checker_response = self.gemini.generate(
            self._build_step_input("checker", seller_state.model_dump_json(indent=2))
        )
        final_state = self._parse_pipeline_state_response(
            checker_response,
            fallback_state=seller_state,
        )
        self._save_intermediate(job_dir, "03_reality_checker.json", final_state)

        self._write_tailoring_md(job_dir, final_state)
        return final_state

    def _build_step_input(self, agent_key: str, input_data: str) -> str:
        prompt = self._extract_agent_prompt(agent_key)
        schema = PipelineState.model_json_schema()
        return (
            f"SYSTEM INSTRUCTIONS:\n{prompt}\n\n"
            "OUTPUT FORMAT:\n"
            "Return JSON only, matching this schema exactly:\n"
            f"{json.dumps(schema, indent=2, ensure_ascii=True)}\n\n"
            f"INPUT DATA:\n{input_data}"
        )

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


def _confidence_from_coverage(coverage: str) -> str:
    if coverage == "full":
        return "strong"
    if coverage == "partial":
        return "moderate"
    return "weak"


def _propose_claim_text(requirement_text: str, evidence_lines: list[str]) -> str:
    if evidence_lines:
        return f"{requirement_text} Evidence includes: {evidence_lines[0]}"
    return f"No direct evidence available yet for: {requirement_text}"


class MatchProposalPipeline(CVTailoringPipeline):
    """Single-call matcher proposal with human review file output."""

    def execute_proposal(self, job_id: str, source: str = "tu_berlin") -> Path:
        job_dir = self.config.pipeline_root / source / job_id
        job_posting = self._load_job_posting(job_dir)
        profile = load_base_profile(self.config.profile_path())
        model = CVModel.from_profile(profile)

        context = self._build_initial_context(job_posting, profile, model)
        logger.info("Running single MATCH proposal step...")
        matcher_state = self.run_step("matcher", context)
        self._save_intermediate(job_dir, "01_matcher.json", matcher_state)

        proposal_path = self._write_match_proposal_md(
            job_dir=job_dir,
            job_id=job_id,
            state=matcher_state,
        )
        return proposal_path

    def _write_match_proposal_md(
        self,
        job_dir: Path,
        job_id: str,
        state: PipelineState,
    ) -> Path:
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)
        proposal_path = planning_dir / "match_proposal.md"

        requirements_by_id = {
            requirement.id: requirement.text for requirement in state.job.requirements
        }
        evidence_by_id = {item.id: item.text for item in state.evidence_items}

        lines = [
            "---",
            "status: proposed",
            f"job_id: {job_id}",
            f"generated: {datetime.now(timezone.utc).isoformat()}",
            "---",
            "",
            f"# Match Proposal: {state.job.title}",
            "",
            "## Requirements Mapping",
            "",
        ]

        summary_candidates: list[str] = []
        for mapping in state.mapping:
            requirement_text = requirements_by_id.get(
                mapping.req_id, "Unknown requirement"
            )
            evidence_lines = [
                evidence_by_id[evidence_id]
                for evidence_id in mapping.evidence_ids
                if evidence_id in evidence_by_id
            ]
            claim_text = _propose_claim_text(requirement_text, evidence_lines)
            confidence = _confidence_from_coverage(mapping.coverage)

            if mapping.coverage in {"full", "partial"}:
                summary_candidates.append(claim_text)

            lines.extend(
                [
                    f"### {mapping.req_id}: {requirement_text} [{mapping.coverage.upper()}]",
                    f"Evidence IDs: {', '.join(mapping.evidence_ids) if mapping.evidence_ids else 'None'}",
                    f"Evidence: {' | '.join(evidence_lines) if evidence_lines else 'No evidence extracted'}",
                    f"Claim: {claim_text}",
                    f"Confidence: {confidence}",
                    "Decision: [ ] approve  [ ] edit  [ ] reject",
                    "Edited Claim:",
                    "Notes:",
                    "",
                ]
            )

        gaps = [
            requirements_by_id.get(mapping.req_id, mapping.req_id)
            for mapping in state.mapping
            if mapping.coverage == "none"
        ]
        lines.extend(["## Gaps (no evidence found)", ""])
        if gaps:
            lines.extend([f"- {gap}" for gap in gaps])
        else:
            lines.append("- No explicit gaps detected by matcher.")

        lines.extend(["", "## Proposed Summary", ""])
        if summary_candidates:
            lines.append(" ".join(summary_candidates[:3]))
        else:
            lines.append("No summary candidate produced. Add one during review.")

        proposal_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return proposal_path


def _extract_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    header_raw = parts[0].replace("---\n", "", 1)
    body = parts[1]
    data: dict[str, str] = {}
    for line in header_raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def _extract_line_value(block: str, prefix: str) -> str:
    for line in block.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_decision(block: str) -> str | None:
    lowered = block.lower()
    if "[x] approve" in lowered:
        return "approved"
    if "[x] edit" in lowered:
        return "edited"
    if "[x] reject" in lowered:
        return "rejected"

    match = re.search(r"Decision:\s*(approved|edited|rejected)", block, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def parse_reviewed_proposal(path: Path) -> ReviewedMapping:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _extract_frontmatter(text)
    job_id = frontmatter.get("job_id", "")
    status = frontmatter.get("status", "proposed")

    heading_pattern = re.compile(
        r"^###\s+((?:R|req_)\d+):\s*(.*?)\s+\[(FULL|PARTIAL|NONE)\]\s*$",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    matches = list(heading_pattern.finditer(body))

    claims: list[ReviewedClaim] = []
    for idx, heading in enumerate(matches):
        start = heading.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        block = body[start:end]
        decision = _parse_decision(block)
        if decision is None:
            continue

        evidence_ids_raw = _extract_line_value(block, "Evidence IDs")
        evidence_ids = [
            item.strip()
            for item in evidence_ids_raw.split(",")
            if item.strip() and item.strip().lower() != "none"
        ]
        claim_text = _extract_line_value(block, "Claim")
        edited_claim = _extract_line_value(block, "Edited Claim")
        notes = _extract_line_value(block, "Notes")

        if decision == "edited" and edited_claim:
            claim_text = edited_claim

        if decision == "approved":
            decision_literal: Literal["approved", "edited", "rejected"] = "approved"
        elif decision == "edited":
            decision_literal = "edited"
        else:
            decision_literal = "rejected"
        claims.append(
            ReviewedClaim(
                req_id=heading.group(1),
                decision=decision_literal,
                claim_text=claim_text,
                evidence_ids=evidence_ids,
                section="summary",
                notes=notes,
            )
        )

    gaps: list[str] = []
    gaps_match = re.search(
        r"##\s+Gaps\s*\(no evidence found\)(.*?)(\n##\s+|\Z)",
        body,
        flags=re.DOTALL,
    )
    if gaps_match:
        for line in gaps_match.group(1).splitlines():
            item = line.strip()
            if item.startswith("- "):
                gaps.append(item[2:].strip())

    summary = ""
    summary_match = re.search(
        r"##\s+Proposed Summary\s*(.*?)(\n##\s+|\Z)",
        body,
        flags=re.DOTALL,
    )
    if summary_match:
        summary = summary_match.group(1).strip()

    if status == "reviewed":
        status_literal: Literal["proposed", "reviewed", "approved"] = "reviewed"
    elif status == "approved":
        status_literal = "approved"
    else:
        status_literal = "proposed"

    return ReviewedMapping(
        job_id=job_id,
        status=status_literal,
        claims=claims,
        gaps=gaps,
        summary=summary,
    )


CVMultiAgentPipeline = CVTailoringPipeline
