"""Persistence for generated documents and their tailored deltas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ai.generate_documents.contracts import (
    DocumentDeltas,
    GeneratedDocuments,
    TextReviewAssistEnvelope,
)
from src.ai.match_skill.storage import MatchArtifactStore


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
                profile_base = json.loads(candidate.read_text(encoding="utf-8"))
            else:
                profile_base = {}

        input_store = match_store or MatchArtifactStore(self.root)
        requirements_raw = requirements or []
        reqs_path = input_store.job_root(source, job_id) / "requirements.json"
        if not requirements_raw and reqs_path.exists():
            requirements_raw = json.loads(reqs_path.read_text(encoding="utf-8"))

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
        root = self.job_root(source, job_id)

        deltas_path = root / "deltas.json"
        self._write_json(deltas_path, deltas.model_dump())

        cv_path = root / "cv.md"
        letter_path = root / "cover_letter.md"
        email_path = root / "email_body.txt"

        cv_path.parent.mkdir(parents=True, exist_ok=True)
        cv_path.write_text(rendered.cv_markdown, encoding="utf-8")
        letter_path.write_text(rendered.letter_markdown, encoding="utf-8")
        email_path.write_text(rendered.email_markdown, encoding="utf-8")

        assist_path = root / "review" / "assist.json"
        self._write_json(assist_path, review_assist.model_dump())

        return {
            "document_deltas_ref": str(deltas_path),
            "cv_markdown_ref": str(cv_path),
            "letter_markdown_ref": str(letter_path),
            "email_markdown_ref": str(email_path),
            "review_assist_ref": str(assist_path),
        }
