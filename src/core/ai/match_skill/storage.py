"""Artifact persistence for the LangGraph-native match skill.

Artifacts are JSON-first on purpose so they can feed LangGraph Studio, a CLI
TUI, or a future custom web UI without forcing markdown parsing into the control
plane.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from src.core.data_manager import DataManager
from src.core.ai.match_skill.contracts import (
    FeedbackItem,
    MatchEnvelope,
    ProfileEvidence,
    RequirementInput,
    ReviewPayload,
    ReviewSurface,
    ReviewSurfaceItem,
)


class MatchArtifactStore:
    """Manage immutable round artifacts plus current refs.

    The store keeps a canonical approved payload, a current review surface, and
    immutable round snapshots for decisions and feedback.
    """

    def __init__(self, root: str | Path = "data/jobs"):
        """Initialize the artifact store.

        Args:
            root: Base directory where match skill artifacts are written.
        """

        self.root = Path(root)
        self.data_manager = DataManager(self.root)

    def job_root(self, source: str, job_id: str) -> Path:
        """Return the root artifact directory for one job."""

        return self.root / source / job_id / "nodes" / "match_skill"

    def next_round_number(self, source: str, job_id: str) -> int:
        """Compute the next immutable round number for a job."""

        rounds_dir = self.job_root(source, job_id) / "review" / "rounds"
        existing = []
        if rounds_dir.exists():
            for path in rounds_dir.glob("round_*"):
                suffix = path.name.replace("round_", "")
                if suffix.isdigit():
                    existing.append(int(suffix))
        return (max(existing) + 1) if existing else 1

    def write_match_round(
        self,
        *,
        source: str,
        job_id: str,
        round_number: int,
        match_result: MatchEnvelope,
        requirements: list[RequirementInput],
        profile_evidence: list[ProfileEvidence],
        regeneration_scope: list[str] | None,
    ) -> dict[str, str]:
        """Persist a model-produced match proposal and review surface.

        Returns:
            Artifact references for the approved payload and review surface.
        """

        job_root = self.job_root(source, job_id)
        approved_path = job_root / "approved" / "state.json"
        review_round_dir = job_root / "review" / "rounds" / f"round_{round_number:03d}"
        current_review_path = job_root / "review" / "current.json"

        self._write_json(approved_path, match_result.model_dump())
        source_hash = self.sha256_file(approved_path)
        review_surface = self.build_review_surface(
            match_result=match_result,
            requirements=requirements,
            profile_evidence=profile_evidence,
            round_number=round_number,
            source_state_hash=source_hash,
            regeneration_scope=regeneration_scope or [],
        )
        round_review_path = review_round_dir / "proposal.json"
        self._write_json(round_review_path, review_surface.model_dump())
        self._write_json(current_review_path, review_surface.model_dump())
        return {
            "approved_match_ref": str(approved_path),
            "review_surface_ref": str(current_review_path),
            "round_review_surface_ref": str(round_review_path),
        }

    def write_review_result(
        self,
        *,
        source: str,
        job_id: str,
        round_number: int,
        review_payload: ReviewPayload,
        feedback_items: list[FeedbackItem],
        routing_decision: str,
    ) -> dict[str, str]:
        """Persist normalized human review results for a completed round.

        Returns:
            Artifact references for the decision and feedback payloads.
        """

        review_round_dir = (
            self.job_root(source, job_id)
            / "review"
            / "rounds"
            / f"round_{round_number:03d}"
        )
        decision_path = review_round_dir / "decision.json"
        feedback_path = review_round_dir / "feedback.json"
        current_decision_path = (
            self.job_root(source, job_id) / "review" / "decision.json"
        )

        decision_payload = {
            "round_number": round_number,
            "source_state_hash": review_payload.source_state_hash,
            "routing_decision": routing_decision,
            "items": [item.model_dump() for item in review_payload.items],
        }
        feedback_payload = {
            "round_number": round_number,
            "routing_decision": routing_decision,
            "feedback": [item.model_dump() for item in feedback_items],
        }

        self._write_json(decision_path, decision_payload)
        self._write_json(current_decision_path, decision_payload)
        self._write_json(feedback_path, feedback_payload)

        # Global propagation of patches to "feed the profile"
        self._propagate_patches_to_global_profile(feedback_items)

        return {
            "review_decision_ref": str(current_decision_path),
            "feedback_ref": str(feedback_path),
        }

    def _propagate_patches_to_global_profile(
        self, feedback_items: list[FeedbackItem]
    ) -> None:
        """Append new patch evidence items to the global persistent profile store."""

        patches_to_add = [
            item.patch_evidence.model_dump()
            for item in feedback_items
            if item.patch_evidence is not None
        ]
        if not patches_to_add:
            return

        # Canonical path for global patches (matching load_profile node)
        global_path = Path(
            "data/reference_data/profile/base_profile/profile_patches.json"
        )
        try:
            current_patches = []
            if global_path.exists():
                current_patches = self.data_manager.read_json_path(global_path)

            if not isinstance(current_patches, list):
                current_patches = []

            seen_ids = {p.get("id") for p in current_patches if isinstance(p, dict)}

            changes = False
            for patch in patches_to_add:
                if patch.get("id") not in seen_ids:
                    current_patches.append(patch)
                    seen_ids.add(patch.get("id"))
                    changes = True

            if changes:
                self.data_manager.write_json_path(global_path, current_patches)
        except Exception as e:
            # We don't want to crash the whole pipeline if global sync fails
            # but we should log it
            import logging

            logging.getLogger(__name__).error(
                f"_propagate_patches_to_global_profile: patch write failed — reviewer feedback was lost: {e}"
            )

    def get_all_feedback_patches(
        self, source: str, job_id: str
    ) -> list[ProfileEvidence]:
        """Collect unique patch-evidence items across all completed rounds."""

        rounds_dir = self.job_root(source, job_id) / "review" / "rounds"
        patches: list[ProfileEvidence] = []
        seen_ids: set[str] = set()
        if not rounds_dir.exists():
            return patches

        for feedback_path in sorted(rounds_dir.glob("round_*/feedback.json")):
            payload = self.load_json(feedback_path)
            for raw_item in payload.get("feedback", []):
                patch = raw_item.get("patch_evidence")
                if not isinstance(patch, dict):
                    continue
                candidate = ProfileEvidence.model_validate(patch)
                if candidate.id in seen_ids:
                    continue
                patches.append(candidate)
                seen_ids.add(candidate.id)
        return patches

    def load_json(self, path: str | Path) -> dict[str, Any]:
        """Load a UTF-8 JSON file from disk."""

        return self.data_manager.read_json_path(path)

    def sha256_file(self, path: str | Path) -> str:
        """Return a ``sha256:...`` digest for a persisted artifact."""

        return self.data_manager.sha256_path(path)

    def build_review_surface(
        self,
        *,
        match_result: MatchEnvelope,
        requirements: list[RequirementInput],
        profile_evidence: list[ProfileEvidence],
        round_number: int,
        source_state_hash: str,
        regeneration_scope: list[str],
    ) -> ReviewSurface:
        """Build the UI-facing JSON review surface for one round."""

        requirement_lookup = {item.id: item for item in requirements}
        evidence_lookup = {item.id: item.description for item in profile_evidence}
        scope_set = set(regeneration_scope)
        rows: list[ReviewSurfaceItem] = []

        for match in match_result.matches:
            requirement = requirement_lookup.get(match.requirement_id)
            rows.append(
                ReviewSurfaceItem(
                    requirement_id=match.requirement_id,
                    requirement_text=requirement.text if requirement else "",
                    priority=requirement.priority if requirement else None,
                    score=match.score,
                    status=match.status,
                    evidence_ids=match.evidence_ids,
                    evidence_texts=[
                        evidence_lookup.get(item, "") for item in match.evidence_ids
                    ],
                    evidence_quotes=match.evidence_quotes,
                    reasoning=match.reasoning,
                    in_regeneration_scope=(
                        not scope_set or match.requirement_id in scope_set
                    ),
                )
            )

        return ReviewSurface(
            round_number=round_number,
            source_state_hash=source_state_hash,
            recommendation=match_result.decision_recommendation,
            total_score=match_result.total_score,
            summary_notes=match_result.summary_notes,
            items=rows,
        )

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        """Write UTF-8 JSON, creating parent directories as needed."""

        self.data_manager.write_json_path(path, payload)
