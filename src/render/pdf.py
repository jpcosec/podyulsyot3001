from pathlib import Path
import importlib

from docx import Document


def extract_docx_text(docx_path: Path) -> str:
    doc = Document(str(docx_path))
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(lines)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext (preferred) or pypdf fallback."""
    import shutil
    import subprocess

    if shutil.which("pdftotext"):
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            capture_output=True,
            text=True,
        )
        return result.stdout

    # Fallback to pypdf / PyPDF2
    reader_mod = (
        importlib.import_module("pypdf")
        if importlib.util.find_spec("pypdf")
        else importlib.import_module("PyPDF2")
    )
    PdfReader = getattr(reader_mod, "PdfReader")
    reader = PdfReader(str(pdf_path))
    lines: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            lines.append(page_text.strip())
    return "\n".join(lines)
