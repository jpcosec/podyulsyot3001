from pathlib import Path
from src.render.pdf import extract_docx_text
from src.render.docx import DocumentRenderer


def test_extract_text_from_docx(tmp_path):
    renderer = DocumentRenderer()
    renderer.render_summary("This is a test summary for extraction.")
    out = tmp_path / "cv.docx"
    renderer.save(out)
    text = extract_docx_text(out)
    assert "test summary" in text.lower()
