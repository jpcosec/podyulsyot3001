"""PDF and DOCX text extraction utilities."""

from __future__ import annotations

import subprocess
from pathlib import Path


def extract_docx_text(docx_path: str | Path) -> str:
    """Extract plain text from a DOCX file via python-docx."""
    try:
        from docx import Document  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError("python-docx is required for DOCX text extraction") from exc

    doc = Document(str(docx_path))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract plain text from a PDF. Prefers pdftotext; falls back to pypdf."""
    path = str(pdf_path)

    try:
        result = subprocess.run(
            ["pdftotext", path, "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    try:
        from pypdf import PdfReader  # type: ignore[import]

        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader as LegacyReader  # type: ignore[import]

        reader = LegacyReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError as exc:
        raise RuntimeError(
            "PDF text extraction requires pdftotext, pypdf, or PyPDF2"
        ) from exc
