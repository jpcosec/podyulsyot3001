import pytest
from pathlib import Path
from src.render.docx import DocumentRenderer
from src.render.styles import CVStyles


def test_renderer_creates_document():
    renderer = DocumentRenderer()
    assert renderer.doc is not None


def test_render_and_save(tmp_path):
    renderer = DocumentRenderer()
    renderer.render_header("Jane Doe", "ML Engineer | Researcher", "jane@example.com | +49 123 456")
    renderer.render_summary("Experienced ML engineer.")
    out = tmp_path / "cv.docx"
    renderer.save(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_styles_has_required_constants():
    assert hasattr(CVStyles, "PRIMARY_COLOR")
    assert hasattr(CVStyles, "FONT_NAME")
    assert hasattr(CVStyles, "SIZE_HEADER")
