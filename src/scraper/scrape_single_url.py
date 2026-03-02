from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag


GERMAN_MARKERS = (
    " bewerbung ",
    " bewerbungsfrist ",
    " aufgaben ",
    " anforderungen ",
    " stellenausschreibung ",
    " wissenschaftliche",
    " ausgeschrieben",
    " deuts",
)

UNAVAILABLE_MARKERS = (
    "job posting is no longer available",
    "die stellenausschreibung ist nicht mehr verfugbar",
    "die stellenausschreibung ist nicht mehr verfügbar",
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_key(value: str) -> str:
    lowered = normalize_text(value).lower()
    return (
        lowered.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def extract_job_id(url: str) -> str:
    match = re.search(r"/(\d+)(?:\?.*)?$", url.strip())
    if not match:
        raise ValueError(f"Could not extract numeric job id from URL: {url}")
    return match.group(1)


def download_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_full_text_markdown(html_content: str, url: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    main = soup.find("main") or soup.find("body") or soup

    lines: list[str] = []
    page_title = (
        normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    )

    lines.append("# Scraped Source Text")
    lines.append("")
    lines.append(f"- URL: {url}")
    lines.append(f"- Retrieved UTC: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    if page_title:
        lines.append("## Page Title")
        lines.append(page_title)
        lines.append("")
    lines.append("## Main Content")

    last_line = ""
    for node in main.find_all(["h1", "h2", "h3", "p", "li", "tr"]):
        rendered = render_node_line(node)
        if not rendered:
            continue
        if rendered == last_line:
            continue
        lines.append(rendered)
        last_line = rendered

    lines.append("")
    return "\n".join(lines)


def render_node_line(node: Tag) -> str:
    name = node.name.lower()
    text = normalize_text(node.get_text(" ", strip=True))
    if not text:
        return ""

    if name == "h1":
        return f"# {text}"
    if name == "h2":
        return f"## {text}"
    if name == "h3":
        return f"### {text}"
    if name == "li":
        return f"- {text}"
    if name == "tr":
        th = node.find("th")
        td = node.find("td")
        if th and td:
            key = normalize_text(th.get_text(" ", strip=True))
            value = normalize_text(td.get_text(" ", strip=True))
            if key and value:
                return f"- {key}: {value}"
        return ""
    return text


def detect_english_status(markdown_text: str) -> dict[str, object]:
    lowered = f" {normalize_key(markdown_text)} "
    marker_hits = sum(lowered.count(marker.strip()) for marker in GERMAN_MARKERS)
    has_umlaut = any(ch in markdown_text for ch in "äöüÄÖÜß")
    is_english = marker_hits <= 1
    return {
        "is_english": is_english,
        "marker_hits": marker_hits,
        "has_umlaut": has_umlaut,
    }


def parse_structured_from_markdown(
    markdown_text: str,
    url: str,
    job_id: str,
) -> dict[str, object]:
    sections = split_markdown_sections(markdown_text)
    facts = extract_facts_from_sections(sections)

    all_text_norm = normalize_key(markdown_text)
    status = (
        "Closed"
        if any(marker in all_text_norm for marker in UNAVAILABLE_MARKERS)
        else "Open"
    )

    title = extract_title_from_sections(sections)
    reference_number = first_non_empty(
        facts.get("reference number", ""),
        extract_by_regex(markdown_text, r"Reference\s+([A-Za-z0-9\-/]+)"),
        extract_by_regex(markdown_text, r"Job Posting\s+([A-Za-z0-9\-/]+)"),
        "Unknown",
    )
    deadline = first_non_empty(
        facts.get("application deadline", ""),
        facts.get("deadline", ""),
        extract_by_regex(markdown_text, r"\b\d{2}\.\d{2}\.\d{4}\b"),
        "Unknown",
    )
    category = first_non_empty(facts.get("category", ""), "Unknown")
    duration = first_non_empty(facts.get("duration", ""), "Unknown")
    salary = first_non_empty(facts.get("salary", ""), "Unknown")
    contact_person = first_non_empty(facts.get("contact person", ""), "Unknown")

    contact_email = extract_by_regex(
        markdown_text,
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    )
    if not contact_email:
        contact_email = "Unknown"

    requirements = collect_section_lines(
        sections,
        aliases=(
            "your profile",
            "profile",
            "requirements",
            "anforderungen",
            "qualifikation",
        ),
    )
    responsibilities = collect_section_lines(
        sections,
        aliases=(
            "your responsibility",
            "responsibilities",
            "tasks",
            "aufgaben",
            "aufgabengebiet",
        ),
    )
    application_instructions = collect_section_lines(
        sections,
        aliases=("how to apply", "bewerbung", "hinweise zur bewerbung", "apply"),
    )

    return {
        "status": status,
        "url": url,
        "job_id": job_id,
        "title": title,
        "reference_number": reference_number,
        "deadline": deadline,
        "category": category,
        "duration": duration,
        "salary": salary,
        "contact_person": contact_person,
        "contact_email": contact_email,
        "requirements": requirements,
        "responsibilities": responsibilities,
        "application_instructions": application_instructions,
    }


def split_markdown_sections(markdown_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "_root"
    sections[current] = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            current = normalize_text(line.lstrip("#").strip())
            sections.setdefault(current, [])
            continue
        if line:
            sections.setdefault(current, []).append(line)
    return sections


def extract_facts_from_sections(sections: dict[str, list[str]]) -> dict[str, str]:
    facts: dict[str, str] = {}
    for lines in sections.values():
        for line in lines:
            raw = line[2:].strip() if line.startswith("- ") else line
            match = re.match(r"([^:]{2,80}):\s*(.+)", raw)
            if not match:
                continue
            key = normalize_key(match.group(1))
            value = normalize_text(match.group(2))
            if key and value and key not in facts:
                facts[key] = value
    return facts


def extract_title_from_sections(sections: dict[str, list[str]]) -> str:
    for heading in sections:
        if heading in {"_root", "Scraped Source Text", "Main Content", "Page Title"}:
            continue
        lowered = normalize_key(heading)
        if "job posting" in lowered or "research" in lowered or "assistant" in lowered:
            return heading
    page_title_lines = sections.get("Page Title", [])
    if page_title_lines:
        title = page_title_lines[0]
        title = title.split("– Job Postings at Technische")[0].strip()
        title = title.split("- Job Postings at Technische")[0].strip()
        return title
    return "Unknown"


def collect_section_lines(
    sections: dict[str, list[str]], aliases: tuple[str, ...]
) -> list[str]:
    alias_keys = [normalize_key(alias) for alias in aliases]
    items: list[str] = []
    seen: set[str] = set()
    for heading, lines in sections.items():
        heading_key = normalize_key(heading)
        if not any(alias in heading_key for alias in alias_keys):
            continue
        for line in lines:
            item = clean_item_line(line)
            if not item:
                continue
            if item in seen:
                continue
            items.append(item)
            seen.add(item)
    return items


def clean_item_line(line: str) -> str:
    value = line.strip()
    if value.startswith("- "):
        value = value[2:].strip()
    value = value.strip()
    if not value:
        return ""
    return value


def first_non_empty(*values: str) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def extract_by_regex(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return ""
    if match.groups():
        return normalize_text(match.group(1))
    return normalize_text(match.group(0))


def to_checklist(lines: list[str], fallback: str) -> str:
    if not lines:
        return f"- [ ] {fallback}"
    return "\n".join([f"- [ ] {line}" for line in lines])


def coerce_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def extract_full_posting_body(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    start_index = 0
    for idx, line in enumerate(lines):
        if line.strip() == "## Main Content":
            start_index = idx + 1
            break

    body_lines = [line for line in lines[start_index:] if line.strip()]
    body_lines = [
        line
        for line in body_lines
        if not line.startswith("- URL:") and not line.startswith("- Retrieved UTC:")
    ]

    if body_lines and body_lines[0].startswith("# "):
        body_lines = body_lines[1:]

    return "\n".join(body_lines).strip()


def render_tracker_markdown(data: dict[str, object], full_text_markdown: str) -> str:
    posting_body = extract_full_posting_body(full_text_markdown)
    
    # If extraction from structured section failed, try raw markdown
    if not posting_body:
        posting_body = full_text_markdown.strip()
    
    # Only as last resort, fall back to filtered checklists
    if not posting_body:
        requirements = coerce_str_list(data.get("requirements"))
        responsibilities = coerce_str_list(data.get("responsibilities"))
        application = coerce_str_list(data.get("application_instructions"))

        requirements_md = to_checklist(requirements, "Review requirements from posting")
        responsibilities_md = to_checklist(
            responsibilities, "Review responsibilities from posting"
        )
        application_md = (
            "\n".join([f"- {line}" for line in application]) or "- Not extracted"
        )
        posting_body = (
            "## Their Requirements (Profile)\n"
            + requirements_md
            + "\n\n## Area of Responsibility (Tasks)\n"
            + responsibilities_md
            + "\n\n## How to Apply (Verbatim)\n"
            + application_md
        )

    return f"""---
status: {data["status"]}
deadline: {data["deadline"]}
reference_number: {data["reference_number"]}
university: TU Berlin
category: {data["category"]}
contact_person: {data["contact_person"]}
contact_email: {data["contact_email"]}
url: {data["url"]}
---

# {data["title"]}

{posting_body}
"""


def run_for_url(
    url: str,
    source: str,
    pipeline_root: Path,
    strict_english: bool,
) -> dict[str, str]:
    job_id = extract_job_id(url)
    job_dir = pipeline_root / source / job_id
    raw_dir = job_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    html_content = download_html(url)
    raw_html_path = raw_dir / "raw.html"
    raw_html_path.write_text(html_content, encoding="utf-8")

    extracted_md = extract_full_text_markdown(html_content, url=url)
    extracted_md_path = raw_dir / "source_text.md"
    extracted_md_path.write_text(extracted_md, encoding="utf-8")

    language = detect_english_status(extracted_md)
    language_path = raw_dir / "language_check.json"
    language_path.write_text(
        json.dumps(language, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if strict_english and not language["is_english"]:
        raise ValueError(
            "Extracted text is not confidently English. "
            + f"See {language_path} and rerun with translated URL/content."
        )

    structured = parse_structured_from_markdown(extracted_md, url=url, job_id=job_id)
    extracted_json_path = raw_dir / "extracted.json"
    extracted_json_path.write_text(
        json.dumps(structured, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    tracker = render_tracker_markdown(structured, extracted_md)
    job_md_path = job_dir / "job.md"
    job_md_path.write_text(tracker, encoding="utf-8")

    return {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "raw_html": str(raw_html_path),
        "source_text_md": str(extracted_md_path),
        "language_check": str(language_path),
        "extracted_json": str(extracted_json_path),
        "job_md": str(job_md_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic scrape pipeline for a specific job URL"
    )
    parser.add_argument("urls", nargs="+", help="One or more full TU Berlin job URLs")
    parser.add_argument("--source", default="tu_berlin", help="Source namespace folder")
    parser.add_argument(
        "--pipeline-root",
        default=os.path.join("data", "pipelined_data"),
        help="Root folder for pipelined data",
    )
    parser.add_argument(
        "--strict-english",
        action="store_true",
        help="Fail when extracted markdown is not confidently English",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline_root = Path(args.pipeline_root).resolve()
    for url in args.urls:
        result = run_for_url(
            url=url,
            source=args.source,
            pipeline_root=pipeline_root,
            strict_english=args.strict_english,
        )

        print(f"[done] job_id={result['job_id']}")
        print(f"[done] html: {result['raw_html']}")
        print(f"[done] source text: {result['source_text_md']}")
        print(f"[done] language check: {result['language_check']}")
        print(f"[done] extracted json: {result['extracted_json']}")
        print(f"[done] tracker: {result['job_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
