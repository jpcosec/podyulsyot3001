from __future__ import annotations

import json
import os
import re
import sys
import argparse
from pathlib import Path

from deep_translator import GoogleTranslator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.scraper.scrape_single_url import (
    coerce_str_list,
    detect_english_status,
    download_html,
    extract_full_text_markdown,
    parse_structured_from_markdown,
    render_tracker_markdown,
)


def _default_pipeline_root() -> Path:
    return REPO_ROOT / "data" / "pipelined_data" / "tu_berlin"


def _iter_job_dirs(pipeline_root: Path, scope: str) -> list[Path]:
    job_dirs: set[Path] = set()

    if scope in {"active", "all"}:
        for path in pipeline_root.glob("*/job.md"):
            if path.is_file() and path.parent.name.isdigit():
                job_dirs.add(path.parent)
        for path in pipeline_root.iterdir():
            if path.is_dir() and path.name.isdigit():
                job_dirs.add(path)

    if scope in {"archive", "all"}:
        archive_root = pipeline_root / "archive"
        if archive_root.exists():
            for path in archive_root.rglob("job.md"):
                if path.is_file():
                    job_dirs.add(path.parent)

    return sorted(job_dirs)


def _resolve_job_id_from_dirname(dirname: str) -> str:
    match = re.search(r"(\d+)", dirname)
    return match.group(1) if match else dirname


def _to_english_job_url(url: str, job_id: str) -> str:
    if "/job-postings/" in url:
        return re.sub(
            r"https?://www\.jobs\.tu-berlin\.de(?:/[a-z]{2})?/job-postings/\d+.*",
            f"https://www.jobs.tu-berlin.de/en/job-postings/{job_id}",
            url,
        )
    return f"https://www.jobs.tu-berlin.de/en/job-postings/{job_id}"


def _translate_markdown_to_english(markdown_text: str) -> str:
    translator = GoogleTranslator(source="auto", target="en")
    translated_lines: list[str] = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip("\n")
        if not line.strip():
            translated_lines.append(line)
            continue

        if line.startswith("- URL:") or line.startswith("- Retrieved UTC:"):
            translated_lines.append(line)
            continue

        prefix = ""
        content = line
        for marker in ("### ", "## ", "# ", "- "):
            if line.startswith(marker):
                prefix = marker
                content = line[len(marker) :]
                break

        stripped = content.strip()
        if not stripped:
            translated_lines.append(line)
            continue

        try:
            translated = translator.translate(stripped)
        except Exception:
            translated = stripped
        translated_lines.append(prefix + translated)

    return "\n".join(translated_lines)


def _extract_url_from_existing_job_md(job_md_path: Path) -> str:
    if not job_md_path.exists():
        return ""
    content = job_md_path.read_text(encoding="utf-8")
    match = re.search(r"^url:\s*(.+)$", content, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _load_or_build_source_text(
    job_dir: Path, url: str, job_id: str
) -> tuple[str, bool]:
    source_text_path = job_dir / "raw" / "source_text.md"
    raw_html_path = job_dir / "raw" / "raw.html"

    if source_text_path.exists():
        source_text = source_text_path.read_text(encoding="utf-8")
        language = detect_english_status(source_text)
        if language["is_english"]:
            return source_text, False

        english_url = _to_english_job_url(url, job_id)
        try:
            english_html = download_html(english_url)
            english_text = extract_full_text_markdown(english_html, url=english_url)
            english_language = detect_english_status(english_text)
            if english_language["is_english"]:
                raw_html_path.parent.mkdir(parents=True, exist_ok=True)
                raw_html_path.write_text(english_html, encoding="utf-8")
                source_text_path.write_text(english_text, encoding="utf-8")
                return english_text, True
        except Exception:
            pass

        translated = _translate_markdown_to_english(source_text)
        source_text_path.write_text(translated, encoding="utf-8")
        return translated, True

    html_candidates = [
        job_dir / "raw" / "raw.html",
        job_dir / "raw" / "page.html",
        job_dir / "raw.html",
        job_dir / "page.html",
    ]
    html_path = next((path for path in html_candidates if path.exists()), None)
    if html_path is None:
        raise FileNotFoundError(
            f"No source_text.md or raw HTML found in {job_dir.as_posix()}"
        )

    html_content = html_path.read_text(encoding="utf-8", errors="ignore")
    source_text = extract_full_text_markdown(html_content, url=url)
    language = detect_english_status(source_text)
    if not language["is_english"]:
        english_url = _to_english_job_url(url, job_id)
        try:
            english_html = download_html(english_url)
            english_text = extract_full_text_markdown(english_html, url=english_url)
            english_language = detect_english_status(english_text)
            if english_language["is_english"]:
                raw_html_path.parent.mkdir(parents=True, exist_ok=True)
                raw_html_path.write_text(english_html, encoding="utf-8")
                source_text = english_text
            else:
                source_text = _translate_markdown_to_english(source_text)
        except Exception:
            source_text = _translate_markdown_to_english(source_text)

    source_text_path.parent.mkdir(parents=True, exist_ok=True)
    source_text_path.write_text(source_text, encoding="utf-8")
    return source_text, True


def _write_summary_json(
    job_dir: Path, structured: dict[str, object], raw_text: str
) -> None:
    summary_payload = {
        "title": structured.get("title", ""),
        "reference_number": structured.get("reference_number", ""),
        "deadline": structured.get("deadline", ""),
        "institution": "TU Berlin",
        "department": "",
        "location": "Berlin, Germany",
        "contact_person": structured.get("contact_person", ""),
        "contact_email": structured.get("contact_email", ""),
        "requirements": structured.get("requirements", []),
        "responsibilities": structured.get("responsibilities", []),
        "themes": [],
        "raw_text": raw_text,
    }
    (job_dir / "summary.json").write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _write_proposal_text(
    job_dir: Path, structured: dict[str, object], url: str
) -> None:
    requirements = coerce_str_list(structured.get("requirements"))
    responsibilities = coerce_str_list(structured.get("responsibilities"))
    requirements_text = "\n".join(f"- {item}" for item in requirements) or "Unknown"
    responsibilities_text = (
        "\n".join(f"- {item}" for item in responsibilities) or "Unknown"
    )

    proposal = (
        "# Proposal Text Extract\n\n"
        f"- Job ID: {job_dir.name}\n"
        f"- URL: {url}\n\n"
        "## Requirements (verbatim extract)\n\n"
        f"{requirements_text}\n\n"
        "## Responsibilities (verbatim extract)\n\n"
        f"{responsibilities_text}\n"
    )
    (job_dir / "proposal_text.md").write_text(proposal, encoding="utf-8")


def regenerate_job_markdown(job_dir: Path) -> dict[str, object]:
    job_id = _resolve_job_id_from_dirname(job_dir.name)
    default_url = f"https://www.jobs.tu-berlin.de/en/job-postings/{job_id}"
    url = _extract_url_from_existing_job_md(job_dir / "job.md") or default_url

    source_text, created_source_text = _load_or_build_source_text(
        job_dir,
        url=url,
        job_id=job_id,
    )
    structured = parse_structured_from_markdown(source_text, url=url, job_id=job_id)

    raw_dir = job_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "extracted.json").write_text(
        json.dumps(structured, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    job_md = render_tracker_markdown(structured, source_text)
    (job_dir / "job.md").write_text(job_md, encoding="utf-8")
    _write_summary_json(job_dir, structured, raw_text=job_md)
    _write_proposal_text(job_dir, structured, url=url)

    return {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "created_source_text": created_source_text,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate job.md, summary.json, and proposal_text.md from raw files"
    )
    parser.add_argument(
        "--pipeline-root",
        default=None,
        help="Path to source-specific pipeline root (default: tu_berlin root)",
    )
    parser.add_argument(
        "--scope",
        choices=["active", "archive", "all"],
        default="active",
        help="Regeneration scope (default: active)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline_root = Path(
        args.pipeline_root or os.getenv("PHD_DATA_DIR", str(_default_pipeline_root()))
    )
    if not pipeline_root.exists():
        print(f"[error] Pipeline directory not found: {pipeline_root}")
        return 1

    job_dirs = _iter_job_dirs(pipeline_root, scope=args.scope)
    if not job_dirs:
        print(
            f"[warn] No job directories found under {pipeline_root} "
            + f"for scope={args.scope}"
        )
        return 0

    successes = 0
    failures = 0
    for job_dir in job_dirs:
        try:
            regenerate_job_markdown(job_dir)
            successes += 1
        except Exception as exc:
            failures += 1
            print(f"[warn] Failed to regenerate {job_dir}: {exc}")

    print(
        f"[done] Regenerated job.md for {successes} jobs under {pipeline_root}"
        + f" (scope={args.scope})"
        + (f" ({failures} failed)" if failures else "")
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
