from __future__ import annotations

import pytest

from src.nodes.render.contract import RenderInputState, RenderedDocumentRef


def test_render_input_state_requires_non_empty_values() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        RenderInputState.model_validate({"source": "", "job_id": "job-1"})


def test_rendered_document_ref_requires_sha256_prefix() -> None:
    with pytest.raises(ValueError, match="sha256"):
        RenderedDocumentRef.model_validate(
            {
                "source_ref": "nodes/generate_documents/proposed/cv.md",
                "rendered_ref": "nodes/render/proposed/cv.md",
                "sha256": "abc",
            }
        )
