"""Parser for FinalMarkdownBundle into annotatable document segments.

Converts the flat markdown strings in a markdown_bundle artifact into
structured DocumentSegment objects that the HITL 3 vim-mode editor can
display and annotate line-by-line.

Three document types are supported, each with its own splitting strategy:

- cv: Pandoc fenced divs (``::: {.job ...}``, ``::: {.education ...}``) are
  parsed as typed segments; text outside fences is split on double newlines.
- letter / email: Split on double newlines into paragraph segments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

DocType = Literal["cv", "letter", "email"]
SegmentType = Literal["paragraph", "job", "education"]

# Matches the opening line of a Pandoc fenced div, e.g.:
#   ::: {.job role="Data Scientist" org="Acme" dates="2020-01 - Present" location=""}
_FENCE_OPEN_RE = re.compile(r'^:::\s*\{\.(\w+)([^}]*)\}', re.MULTILINE)
_FENCE_CLOSE_STR = "\n:::"


@dataclass
class DocumentSegment:
    """One annotatable unit within a displayed document.

    Args:
        segment_id: Stable patch target, e.g. ``"cv:job:0"``, ``"letter:paragraph:2"``.
        doc_type: Which document this segment belongs to.
        segment_type: Structural type of the segment.
        raw_text: Original text as it appears in the bundle (used for patch payloads).
        display_lines: Human-readable lines shown in the editor widget.
        line_start: Index of the first line in the document's flat line list.
        line_end: Index of the last line (inclusive).
        meta: Parsed fence attributes for job/education segments, empty otherwise.
    """

    segment_id: str
    doc_type: DocType
    segment_type: SegmentType
    raw_text: str
    display_lines: list[str]
    line_start: int
    line_end: int
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """All segments for one document tab plus a flat line list for the cursor.

    Args:
        doc_type: Document type identifier.
        segments: Ordered list of annotatable segments.
        all_lines: Flat list of display lines across all segments.
                   Line index ``n`` maps to a segment via ``segment_for_line(n)``.
    """

    doc_type: DocType
    segments: list[DocumentSegment] = field(default_factory=list)
    all_lines: list[str] = field(default_factory=list)

    def segment_for_line(self, line_idx: int) -> DocumentSegment | None:
        """Return the segment that owns ``line_idx``, or None if out of range."""
        for seg in self.segments:
            if seg.line_start <= line_idx <= seg.line_end:
                return seg
        return None

    def segments_in_range(self, start: int, end: int) -> list[DocumentSegment]:
        """Return all segments that overlap the line range ``[start, end]``."""
        lo, hi = min(start, end), max(start, end)
        return [s for s in self.segments if s.line_end >= lo and s.line_start <= hi]


def parse_bundle(bundle: dict[str, Any]) -> dict[DocType, ParsedDocument]:
    """Parse a FinalMarkdownBundle dict into three ParsedDocuments.

    Args:
        bundle: The ``markdown_bundle`` artifact dict with keys
                ``cv_full_md``, ``letter_full_md``, ``email_body_md``.

    Returns:
        Dict keyed by doc_type with one ParsedDocument per document.
    """
    return {
        "cv": _parse_cv(bundle.get("cv_full_md", "")),
        "letter": _parse_paragraphs("letter", bundle.get("letter_full_md", "")),
        "email": _parse_paragraphs("email", bundle.get("email_body_md", "")),
    }


# ---------------------------------------------------------------------------
# CV parser — handles Pandoc fenced divs
# ---------------------------------------------------------------------------


def _parse_cv(text: str) -> ParsedDocument:
    """Parse CV markdown with Pandoc fence blocks into typed segments."""
    doc = ParsedDocument(doc_type="cv")
    line_cursor = 0
    text_cursor = 0
    fence_counters: dict[str, int] = {}
    para_idx = 0

    for match in _FENCE_OPEN_RE.finditer(text):
        before = text[text_cursor : match.start()].strip()
        if before:
            for seg in _make_paragraph_segments("cv", before, para_idx, line_cursor):
                _append_segment(doc, seg)
                line_cursor += len(seg.display_lines)
                para_idx += 1

        seg_type = match.group(1)
        close_pos = text.find(_FENCE_CLOSE_STR, match.end())
        if close_pos == -1:
            text_cursor = match.start()
            break
        fence_end = close_pos + len(_FENCE_CLOSE_STR)
        raw_fence = text[match.start() : fence_end]

        idx = fence_counters.get(seg_type, 0)
        fence_counters[seg_type] = idx + 1

        meta = _parse_fence_attrs(match.group(2))
        display_lines = _fence_to_display_lines(raw_fence, seg_type, meta)

        seg = DocumentSegment(
            segment_id=f"cv:{seg_type}:{idx}",
            doc_type="cv",
            segment_type=seg_type,  # type: ignore[arg-type]
            raw_text=raw_fence,
            display_lines=display_lines,
            line_start=line_cursor,
            line_end=line_cursor + len(display_lines) - 1,
            meta=meta,
        )
        _append_segment(doc, seg)
        line_cursor += len(display_lines)
        text_cursor = fence_end

    remaining = text[text_cursor:].strip()
    if remaining:
        for seg in _make_paragraph_segments("cv", remaining, para_idx, line_cursor):
            _append_segment(doc, seg)
            line_cursor += len(seg.display_lines)

    return doc


# ---------------------------------------------------------------------------
# Letter / email parser — paragraph splitting only
# ---------------------------------------------------------------------------


def _parse_paragraphs(doc_type: DocType, text: str) -> ParsedDocument:
    """Parse a flat markdown string into paragraph segments split on blank lines."""
    doc = ParsedDocument(doc_type=doc_type)
    line_cursor = 0
    for seg in _make_paragraph_segments(doc_type, text, 0, line_cursor):
        _append_segment(doc, seg)
        line_cursor += len(seg.display_lines)
    return doc


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_paragraph_segments(
    doc_type: DocType,
    text: str,
    start_idx: int,
    line_cursor: int,
) -> list[DocumentSegment]:
    """Split text on blank lines and return one DocumentSegment per paragraph."""
    raw_paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    segments = []
    for offset, raw in enumerate(raw_paragraphs):
        lines = raw.splitlines()
        seg = DocumentSegment(
            segment_id=f"{doc_type}:paragraph:{start_idx + offset}",
            doc_type=doc_type,
            segment_type="paragraph",
            raw_text=raw,
            display_lines=lines,
            line_start=line_cursor,
            line_end=line_cursor + len(lines) - 1,
        )
        segments.append(seg)
        line_cursor += len(lines)
    return segments


def _append_segment(doc: ParsedDocument, seg: DocumentSegment) -> None:
    """Add segment to doc and extend the flat line list."""
    doc.segments.append(seg)
    doc.all_lines.extend(seg.display_lines)


def _fence_to_display_lines(raw: str, seg_type: str, meta: dict[str, Any]) -> list[str]:
    """Render a Pandoc fence block as human-readable display lines.

    The opening ``:::`` and closing ``:::`` markers are replaced with a
    readable header line, and content lines are preserved with indentation.
    """
    lines: list[str] = []

    if seg_type == "job":
        role = meta.get("role", "")
        org = meta.get("org", "")
        dates = meta.get("dates", "")
        header = "  ·  ".join(part for part in (role, org, dates) if part)
        lines.append(header or "Job")
    elif seg_type == "education":
        degree = meta.get("degree", "")
        spec = meta.get("specialization", "")
        institution = meta.get("institution", "")
        dates = meta.get("dates", "")
        header = "  ·  ".join(part for part in (degree, spec, institution, dates) if part)
        lines.append(header or "Education")
    else:
        lines.append(seg_type.title())

    # Content lines between fences (bullet points, detail lines)
    inside = False
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith(":::"):
            inside = not inside
            continue
        if inside and stripped:
            lines.append(f"  {stripped}")

    return lines


def _parse_fence_attrs(attrs_str: str) -> dict[str, Any]:
    """Parse ``key="value"`` pairs from a Pandoc fence attribute string."""
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r'(\w+)="([^"]*)"', attrs_str)
    }
