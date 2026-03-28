"""Render motivation letter markdown to PDF for a given job.

Usage:
    python -m src.cli.render_letter --source tu_berlin --job-id 201553
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.core.tools.render.letter import convert_docx_to_pdf, render_letter_docx


def render_letter(source: str, job_id: str) -> Path:
    app_dir = Path(f"data/jobs/{source}/{job_id}/application")
    md_path = app_dir / "motivation_letter.md"
    if not md_path.exists():
        raise FileNotFoundError(f"motivation_letter.md not found at {md_path}")

    build_dir = Path(f"data/jobs/{source}/{job_id}/render_build/letter")
    build_dir.mkdir(parents=True, exist_ok=True)

    docx_path = render_letter_docx(md_path, build_dir / "motivation_letter.docx")
    pdf_path = convert_docx_to_pdf(docx_path, build_dir)

    dest = app_dir / "motivation_letter.pdf"
    dest.write_bytes(pdf_path.read_bytes())
    print(f"Letter written to {dest}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Render motivation letter PDF.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    render_letter(args.source, args.job_id)


if __name__ == "__main__":
    main()
