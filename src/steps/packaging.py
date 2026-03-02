"""Packaging step: Merge rendered PDFs into final submission document.

This step combines all rendered outputs (CV, motivation letter, etc.) into
a single Final_Application.pdf file suitable for submission.

Reads:
- output/cv.pdf — Rendered CV
- output/motivation_letter.pdf — Rendered motivation letter (if it exists)

Produces:
- output/Final_Application.pdf — Merged and optionally compressed PDF
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from src.steps import StepResult
from src.utils.comments import append_to_comment_log, extract_comments
from src.utils.state import JobState

logger = logging.getLogger(__name__)


def run(
    state: JobState,
    *,
    force: bool = False,
    output_name: str = "Final_Application.pdf",
) -> StepResult:
    """
    Merge all output PDFs into final submission document.

    Combines rendered CV and motivation letter (if available) into a single PDF.
    Optionally compresses the output to stay under 5MB for submission.

    Args:
        state: JobState instance for the target job
        force: Re-run even if outputs already exist
        output_name: Name of the final output file (default: "Final_Application.pdf")

    Returns:
        StepResult with status, produced files, comments_found, message

    Reads:
    - output/cv.pdf — required
    - output/motivation_letter.pdf — optional
    """
    # Check if step already complete and not force
    if not force and state.step_complete("packaging"):
        return StepResult(
            status="skipped",
            produced=[],
            comments_found=0,
            message=f"Packaging already complete for job {state.job_id}",
        )

    produced: list[str] = []
    comments_found = 0

    try:
        # Collect PDFs to merge
        output_dir = state.artifact_path("output")
        if not output_dir.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"output/ directory not found for job {state.job_id}. "
                "Run 'render' first.",
            )

        cv_pdf = output_dir / "cv.pdf"
        if not cv_pdf.exists():
            return StepResult(
                status="error",
                produced=[],
                comments_found=0,
                message=f"output/cv.pdf not found for job {state.job_id}. "
                "Run 'render' first.",
            )

        # Gather PDFs to merge
        pdfs_to_merge = [cv_pdf]
        motivation_pdf = output_dir / "motivation_letter.pdf"
        if motivation_pdf.exists():
            pdfs_to_merge.append(motivation_pdf)

        # Extract comments for feedback loop (from rendered files)
        comments_sources = pdfs_to_merge
        comments = _extract_comments_from_files(comments_sources, state.job_dir)
        comments_found = len(comments)

        # Merge PDFs
        final_pdf = output_dir / output_name
        _merge_pdfs(pdfs_to_merge, final_pdf)

        produced.append(f"output/{output_name}")

        # Log comments to job-level comment log
        log_path = state.artifact_path(".metadata/comments.jsonl")
        append_to_comment_log(log_path, "packaging", comments)

        return StepResult(
            status="ok",
            produced=produced,
            comments_found=comments_found,
            message=f"Merged {len(pdfs_to_merge)} PDF(s) into {output_name} for job {state.job_id}",
        )

    except Exception as e:
        logger.exception(f"Failed to package outputs for job {state.job_id}")
        return StepResult(
            status="error",
            produced=produced,
            comments_found=comments_found,
            message=f"Failed to package outputs: {e}",
        )


# ── Helpers ──


def _merge_pdfs(pdf_paths: list[Path], output_path: Path) -> None:
    """
    Merge multiple PDFs into a single file.

    Uses PyPDF2 for merging and ghostscript for compression.

    Args:
        pdf_paths: List of PDF paths to merge (in order)
        output_path: Path to write final merged PDF

    Raises:
        ValueError: If pdf_paths is empty
        RuntimeError: If merge or compression fails
    """
    if not pdf_paths:
        raise ValueError("No PDFs provided to merge")

    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        raise RuntimeError(
            "PyPDF2 not installed. Install with: pip install PyPDF2"
        )

    # Merge PDFs
    merger = PdfMerger()
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            logger.warning(f"PDF not found, skipping: {pdf_path}")
            continue
        logger.info(f"Adding to merge: {pdf_path.name}")
        merger.append(str(pdf_path))

    if merger.pages:  # Only write if we have pages
        # Write to temporary uncompressed file
        temp_path = output_path.parent / f"{output_path.stem}_uncompressed.pdf"
        merger.write(str(temp_path))
        merger.close()
        logger.info(f"Merged PDF written to {temp_path}")

        # Try to compress
        try:
            _compress_pdf(temp_path, output_path, resolution="ebook")
        except Exception as compress_error:
            # If compression fails, use uncompressed version
            logger.warning(
                f"Compression failed: {compress_error}. "
                f"Using uncompressed PDF."
            )
            temp_path.rename(output_path)
            return

        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
    else:
        merger.close()
        raise RuntimeError("No valid PDFs found to merge")


def _compress_pdf(
    input_path: Path, output_path: Path, resolution: str = "ebook"
) -> None:
    """
    Compress a PDF using ghostscript.

    Args:
        input_path: Path to input PDF
        output_path: Path to output compressed PDF
        resolution: Compression level ('screen', 'ebook', 'printer', 'prepress')

    Raises:
        RuntimeError: If ghostscript not found or compression fails
    """
    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{resolution}",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    logger.info(f"Compressing PDF with {resolution} settings...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Compression complete. Final size: {size_mb:.2f} MB")

        # If still too large, try heavier compression
        if size_mb > 5.0:
            logger.warning(
                f"PDF size {size_mb:.2f} MB exceeds 5 MB limit. "
                f"Trying heavier compression..."
            )
            _compress_pdf(input_path, output_path, resolution="screen")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ghostscript compression failed: {e.stderr.decode()}")
    except FileNotFoundError:
        raise RuntimeError(
            "ghostscript (gs) not found. Install with: apt-get install ghostscript"
        )


def _extract_comments_from_files(paths: list[Path], job_dir: Path) -> list:
    """
    Extract comments from multiple files.

    Note: PDFs don't typically contain HTML comments, so this is a placeholder
    for consistency with other steps.

    Args:
        paths: List of file paths to extract comments from
        job_dir: Job directory for relative path calculation

    Returns:
        List of InlineComment objects
    """
    # PDF files don't have HTML comments, so return empty list
    # This is here for API consistency with other steps
    return []
