"""Persistence for generated documents and their tailored deltas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.data_manager import DataManager
from src.core.ai.generate_documents.contracts import (
    DocumentDeltas,
    GeneratedDocuments,
    TextReviewAssistEnvelope,
)
from src.core.ai.match_skill.storage import MatchArtifactStore


class DocumentArtifactStore(MatchArtifactStore):
    """Artifact store extension for document generation outputs."""

    def load_generation_inputs(
        self,
        *,
        source: str,
        job_id: str,
        match_store: MatchArtifactStore | None = None,
        profile_base_data: dict[str, Any] | None = None,
        requirements: list[dict[str, Any]] | None = None,
        profile_path: str
        | Path = "data/reference_data/profile/base_profile/profile_base_data.json",
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], str]:
        """Load primitive inputs required by the graph generation node."""

        profile_base = profile_base_data
        if not profile_base:
            candidate = Path(profile_path)
            if candidate.exists():
                profile_base = self.data_manager.read_json_path(candidate)
            else:
                profile_base = {}

        input_store = match_store or MatchArtifactStore(self.root)
        requirements_raw = requirements or []
        reqs_path = input_store.job_root(source, job_id) / "requirements.json"
        if not requirements_raw and reqs_path.exists():
            requirements_raw = self.data_manager.read_json_path(reqs_path)

        approved_path = input_store.job_root(source, job_id) / "approved" / "state.json"
        approved_match_raw = input_store.load_json(approved_path)
        approved_matches_raw = (
            approved_match_raw.get("matches")
            if isinstance(approved_match_raw, dict)
            else []
        )
        source_hash = input_store.sha256_file(approved_path)
        return profile_base, requirements_raw, approved_matches_raw, source_hash

    def job_root(self, source: str, job_id: str) -> Path:
        """Return the root artifact directory for the generate_documents node."""
        return self.root / source / job_id / "nodes" / "generate_documents"

    def write_document_payload(
        self,
        *,
        source: str,
        job_id: str,
        deltas: DocumentDeltas,
        rendered: GeneratedDocuments,
        review_assist: TextReviewAssistEnvelope,
    ) -> dict[str, str]:
        """Persist generated document artifacts.

        Returns:
            Artifact references for deltas, rendered markdown, and review assist.
        """
        deltas_path = self.data_manager.write_json_artifact(
            source=source,
            job_id=job_id,
            node_name="generate_documents",
            stage="proposed",
            filename="deltas.json",
            data=deltas.model_dump(),
        )
        cv_path = self.data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="generate_documents",
            stage="proposed",
            filename="cv.md",
            content=rendered.cv_markdown,
        )
        letter_path = self.data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="generate_documents",
            stage="proposed",
            filename="cover_letter.md",
            content=rendered.letter_markdown,
        )
        email_path = self.data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="generate_documents",
            stage="proposed",
            filename="email_body.txt",
            content=rendered.email_markdown,
        )
        assist_path = self.data_manager.write_json_artifact(
            source=source,
            job_id=job_id,
            node_name="generate_documents",
            stage="review",
            filename="assist.json",
            data=review_assist.model_dump(),
        )

        return {
            "document_deltas_ref": str(deltas_path),
            "cv_markdown_ref": str(cv_path),
            "letter_markdown_ref": str(letter_path),
            "email_markdown_ref": str(email_path),
            "review_assist_ref": str(assist_path),
        }
