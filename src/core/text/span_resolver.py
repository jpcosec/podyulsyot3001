"""Deterministic text span resolution service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class SpanResolution:
    found: bool
    exact_quote: str
    normalized_quote: str
    start_line: int | None
    end_line: int | None
    start_offset: int | None
    end_offset: int | None
    preview_snippet: str | None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_ignore_case(text: str) -> str:
    return _normalize(text).lower()


def resolve_span(source_text: str, exact_quote: str | None) -> SpanResolution:
    if not exact_quote or not exact_quote.strip():
        return _not_found("", "")

    normalized_quote = _normalize(exact_quote)
    if not normalized_quote:
        return _not_found(exact_quote, "")

    normalized_source = _normalize(source_text)
    normalized_source_lower = normalized_source.lower()

    match_start = normalized_source_lower.find(normalized_quote.lower())
    if match_start == -1:
        return _not_found(exact_quote, normalized_quote)

    match_end = match_start + len(normalized_quote)
    original_start, original_end = _map_normalized_to_original(
        source_text, match_start, match_end
    )
    original_exact = source_text[original_start:original_end]

    lines = source_text.split("\n")
    start_line = _offset_to_line(lines, original_start)
    end_line = _offset_to_line(lines, original_end - 1)

    preview = _build_preview(source_text, original_start, original_end)

    return SpanResolution(
        found=True,
        exact_quote=original_exact,
        normalized_quote=normalized_quote,
        start_line=start_line,
        end_line=end_line,
        start_offset=original_start,
        end_offset=original_end,
        preview_snippet=preview,
    )


def _not_found(exact_quote: str, normalized_quote: str) -> SpanResolution:
    return SpanResolution(
        found=False,
        exact_quote=exact_quote,
        normalized_quote=normalized_quote,
        start_line=None,
        end_line=None,
        start_offset=None,
        end_offset=None,
        preview_snippet=None,
    )


def _map_normalized_to_original(
    source_text: str, norm_start: int, norm_end: int
) -> tuple[int, int]:
    norm_pos = 0
    orig_pos = 0
    orig_start = 0
    orig_end = 0
    in_whitespace = False

    while orig_pos <= len(source_text):
        if norm_pos == norm_start:
            orig_start = orig_pos
        if norm_pos == norm_end:
            orig_end = orig_pos
            break

        if orig_pos >= len(source_text):
            break

        char = source_text[orig_pos]
        is_ws = char in ("\r", "\n", "\t", " ")

        if is_ws:
            if not in_whitespace:
                in_whitespace = True
                norm_pos += 1
        else:
            in_whitespace = False
            norm_pos += 1

        orig_pos += 1

    if norm_pos < norm_end and orig_end == 0:
        orig_end = len(source_text)

    return orig_start, orig_end


def _offset_to_line(lines: list[str], char_offset: int) -> int:
    current_offset = 0
    for line_idx, line in enumerate(lines):
        line_length = len(line)
        if current_offset <= char_offset < current_offset + line_length:
            return line_idx + 1
        current_offset += line_length + 1
    return len(lines)


def _build_preview(source_text: str, match_start: int, match_end: int) -> str | None:
    prefix_len = 30
    suffix_len = 30
    source_len = len(source_text)

    if match_start < prefix_len and match_end >= source_len - suffix_len:
        return None

    prefix_start = max(0, match_start - prefix_len)
    prefix_text = source_text[prefix_start:match_start]

    suffix_end = min(source_len, match_end + suffix_len)
    suffix_text = source_text[match_end:suffix_end]

    if prefix_start > 0:
        prefix_text = "..." + prefix_text
    if suffix_end < source_len:
        suffix_text += "..."

    return prefix_text + source_text[match_start:match_end] + suffix_text
