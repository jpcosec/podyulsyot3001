"""Match proposal pipeline extracted from src.utils.pipeline."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.graph.parsers.claim_builder import (
    _confidence_from_coverage,
    _valid_evidence_ids,
    build_claim_text,
)
from src.graph.parsers.proposal_parser import parse_reviewed_proposal
from src.graph.pipelines.tailoring import CVTailoringPipeline
from src.models.pipeline_contract import PipelineState, ReviewedClaim
from src.utils.comments import extract_comments
from src.utils.loaders.profile_loader import load_base_profile
from src.utils.model import CVModel

logger = logging.getLogger(__name__)


class MatchProposalPipeline(CVTailoringPipeline):
    """Single-call matcher proposal with human review file output."""

    def execute_proposal(self, job_id: str, source: str = "tu_berlin") -> Path:
        job_dir = self.config.pipeline_root / source / job_id
        job_posting = self.load_job_posting(job_dir)
        profile = load_base_profile(self.config.profile_path())
        model = CVModel.from_profile(profile)

        proposal_path = job_dir / "planning" / "match_proposal.md"
        revision_payload, reviewed_claims_by_req = self._load_revision_context(
            job_dir,
            proposal_path,
        )

        context = self.build_initial_context(job_posting, profile, model)
        matcher_input = self._build_matcher_input(context, revision_payload)
        logger.info("Running single MATCH proposal step...")
        matcher_state = self.call_agent("matcher", matcher_input)
        self._save_intermediate(job_dir, "01_matcher.json", matcher_state)

        proposal_path = self._write_match_proposal_md(
            job_dir=job_dir,
            job_id=job_id,
            state=matcher_state,
            reviewed_claims_by_req=reviewed_claims_by_req,
        )
        return proposal_path

    def _load_revision_context(
        self,
        job_dir: Path,
        proposal_path: Path,
    ) -> tuple[dict[str, Any] | None, dict[str, ReviewedClaim]]:
        if not proposal_path.exists():
            return None, {}

        previous_text = proposal_path.read_text(encoding="utf-8")
        comments = extract_comments(proposal_path, job_dir=job_dir)
        reviewed_mapping = parse_reviewed_proposal(proposal_path)
        reviewed_claims = reviewed_mapping.claims
        by_req = {claim.req_id: claim for claim in reviewed_claims}

        payload: dict[str, Any] = {
            "previous_match_proposal_markdown": previous_text,
            "previous_reviewed_claims": [
                claim.model_dump() for claim in reviewed_claims
            ],
            "user_comments": [
                {
                    "file": comment.file,
                    "line": comment.line,
                    "text": comment.text,
                    "context": comment.context,
                }
                for comment in comments
            ],
        }
        return payload, by_req

    @staticmethod
    def _build_matcher_input(
        base_context: str,
        revision_payload: dict[str, Any] | None,
    ) -> str:
        if not revision_payload:
            return base_context

        revision_directives = "\n".join(
            [
                "REVISION DIRECTIVES:",
                "- Keep approved requirements unchanged.",
                "- Remove rejected requirements from the revised proposal.",
                "- Regenerate evidence for requirements marked as edited.",
                "- Use user comments as mandatory correction context.",
                "- Ensure every Evidence ID references evidence available in this run.",
            ]
        )
        return (
            f"{base_context}\n\n"
            "REVISION CONTEXT (PREVIOUS RESULT + USER COMMENTS):\n"
            f"{json.dumps(revision_payload, indent=2, ensure_ascii=True)}\n\n"
            f"{revision_directives}"
        )

    @staticmethod
    def _archive_existing_proposal(proposal_path: Path) -> None:
        if not proposal_path.exists():
            return

        round_re = re.compile(r"^match_proposal\.round(\d+)\.md$")
        max_round = 0
        for path in proposal_path.parent.glob("match_proposal.round*.md"):
            match = round_re.match(path.name)
            if match:
                max_round = max(max_round, int(match.group(1)))

        next_round = max_round + 1
        archived = proposal_path.parent / f"match_proposal.round{next_round}.md"
        proposal_path.rename(archived)

    @staticmethod
    def _llm_claim_for_mapping(state: PipelineState, req_id: str) -> str | None:
        for claim in state.proposed_claims:
            if claim.id == req_id:
                return claim.claim_text
        return None

    def _write_match_proposal_md(
        self,
        job_dir: Path,
        job_id: str,
        state: PipelineState,
        reviewed_claims_by_req: dict[str, ReviewedClaim] | None = None,
    ) -> Path:
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)
        proposal_path = planning_dir / "match_proposal.md"
        self._archive_existing_proposal(proposal_path)

        requirements_by_id = {
            requirement.id: requirement.text for requirement in state.job.requirements
        }
        evidence_by_id = {item.id: item.text for item in state.evidence_items}
        reviewed_claims_by_req = reviewed_claims_by_req or {}

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
        included_mappings: list[Any] = []
        for mapping in state.mapping:
            prior_claim = reviewed_claims_by_req.get(mapping.req_id)
            if prior_claim is not None and prior_claim.decision == "rejected":
                continue

            requirement_text = requirements_by_id.get(
                mapping.req_id, "Unknown requirement"
            )
            fallback_ids = prior_claim.evidence_ids if prior_claim is not None else []
            evidence_ids = _valid_evidence_ids(
                mapping.evidence_ids,
                fallback_ids,
                evidence_by_id,
            )
            evidence_lines = [
                evidence_by_id[evidence_id]
                for evidence_id in evidence_ids
                if evidence_id in evidence_by_id
            ]

            if prior_claim is not None and prior_claim.decision == "approved":
                claim_text = prior_claim.claim_text
                decision_line = "Decision: [x] approve  [ ] edit  [ ] reject"
                notes_line = (
                    f"Notes: {prior_claim.notes}" if prior_claim.notes else "Notes:"
                )
            else:
                edited_claim = (
                    prior_claim.claim_text
                    if prior_claim is not None and prior_claim.decision == "edited"
                    else None
                )
                claim_text = build_claim_text(
                    requirement_text,
                    evidence_lines,
                    llm_claim=self._llm_claim_for_mapping(state, mapping.req_id),
                    edited_claim=edited_claim,
                )
                decision_line = "Decision: [ ] approve  [ ] edit  [ ] reject"
                notes_line = (
                    f"Notes: {prior_claim.notes}"
                    if prior_claim and prior_claim.notes
                    else "Notes:"
                )

            confidence = _confidence_from_coverage(mapping.coverage)
            included_mappings.append(mapping)

            if mapping.coverage in {"full", "partial"}:
                summary_candidates.append(claim_text)

            lines.extend(
                [
                    f"### {mapping.req_id}: {requirement_text} [{mapping.coverage.upper()}]",
                    f"Evidence IDs: {', '.join(evidence_ids) if evidence_ids else 'None'}",
                    f"Evidence: {' | '.join(evidence_lines) if evidence_lines else 'No evidence extracted'}",
                    f"Claim: {claim_text}",
                    f"Confidence: {confidence}",
                    decision_line,
                    "Edited Claim:",
                    notes_line,
                    "",
                ]
            )

        gaps = [
            requirements_by_id.get(mapping.req_id, mapping.req_id)
            for mapping in included_mappings
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
