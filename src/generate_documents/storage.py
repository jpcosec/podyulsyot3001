"""Persistence for generated documents and their tailored deltas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.generate_documents.contracts import DocumentDeltas, GeneratedDocuments, TextReviewAssistEnvelope
from src.match_skill.storage import MatchArtifactStore


class DocumentArtifactStore(MatchArtifactStore):
    """Artifact store extension for document generation outputs."""

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
        
        # 1. Deltas (raw structured output)
        deltas_path = root / "deltas.json"
        self._write_json(deltas_path, deltas.model_dump())
        
        # 2. Rendered MD
        cv_path = root / "cv.md"
        letter_path = root / "cover_letter.md"
        email_path = root / "email_body.txt"
        
        cv_path.parent.mkdir(parents=True, exist_ok=True)
        cv_path.write_text(rendered.cv_markdown, encoding="utf-8")
        letter_path.write_text(rendered.letter_markdown, encoding="utf-8")
        email_path.write_text(rendered.email_markdown, encoding="utf-8")
        
        # 3. Review indicators
        assist_path = root / "review" / "assist.json"
        self._write_json(assist_path, review_assist.model_dump())

        return {
            "document_deltas_ref": str(deltas_path),
            "cv_markdown_ref": str(cv_path),
            "letter_markdown_ref": str(letter_path),
            "email_markdown_ref": str(email_path),
            "review_assist_ref": str(assist_path),
        }
