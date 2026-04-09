"""Tests for the HITL 3 document parser."""

from __future__ import annotations

from src.review_ui.document_parser import (
    DocumentSegment,
    ParsedDocument,
    parse_bundle,
    _parse_cv,
    _parse_paragraphs,
)

# ---------------------------------------------------------------------------
# Fixtures — representative data matching the real artifact shape
# ---------------------------------------------------------------------------

CV_MD = (
    "Highly proficient in Python, scikit-learn, and SQL for data analysis.\n\n"
    '::: {.job role="Data Scientist" org="TestCorp GmbH" dates="2020-01 - Present" location=""}\n'
    "- Built and deployed ML pipelines using Python and scikit-learn.\n"
    "- Developed SQL-based reporting dashboards in Power BI.\n"
    ":::\n\n"
    '::: {.education degree="M.Sc. Computer Science" specialization="Machine Learning" '
    'institution="Test University" dates="Present" location=""}\n'
    ":::\n\n"
    "- **Programming:** Python, SQL\n"
    "- **Ml:** scikit-learn, Machine Learning"
)

LETTER_MD = (
    "Dear Hiring Team, I am writing to express my interest in the position.\n\n"
    "My expertise encompasses the full ML lifecycle, from data acquisition to deployment.\n\n"
    "Thank you for considering my application. I look forward to speaking with you."
)

BUNDLE = {
    "cv_full_md": CV_MD,
    "letter_full_md": LETTER_MD,
    "email_body_md": "Short email body.\n\nBest regards.",
    "rendering_metadata": {"job_title_original": "Data Scientist"},
}


# ---------------------------------------------------------------------------
# parse_bundle
# ---------------------------------------------------------------------------


def test_parse_bundle_returns_all_three_docs() -> None:
    result = parse_bundle(BUNDLE)
    assert set(result.keys()) == {"cv", "letter", "email"}
    for doc in result.values():
        assert isinstance(doc, ParsedDocument)
        assert len(doc.segments) > 0
        assert len(doc.all_lines) > 0


# ---------------------------------------------------------------------------
# CV parsing
# ---------------------------------------------------------------------------


def test_cv_segments_types() -> None:
    doc = _parse_cv(CV_MD)
    types = [s.segment_type for s in doc.segments]
    assert "paragraph" in types
    assert "job" in types
    assert "education" in types


def test_cv_segment_ids_are_unique() -> None:
    doc = _parse_cv(CV_MD)
    ids = [s.segment_id for s in doc.segments]
    assert len(ids) == len(set(ids))


def test_cv_job_segment_has_meta() -> None:
    doc = _parse_cv(CV_MD)
    job_seg = next(s for s in doc.segments if s.segment_type == "job")
    assert job_seg.meta["role"] == "Data Scientist"
    assert job_seg.meta["org"] == "TestCorp GmbH"
    assert job_seg.meta["dates"] == "2020-01 - Present"


def test_cv_job_display_lines_humanised() -> None:
    doc = _parse_cv(CV_MD)
    job_seg = next(s for s in doc.segments if s.segment_type == "job")
    # Header line should contain role and org
    assert "Data Scientist" in job_seg.display_lines[0]
    assert "TestCorp GmbH" in job_seg.display_lines[0]
    # Bullet lines should be present and indented
    bullet_lines = [l for l in job_seg.display_lines[1:] if l.strip()]
    assert len(bullet_lines) >= 1
    assert all(l.startswith("  ") for l in bullet_lines)


def test_cv_education_segment_no_raw_fence_markers_in_display() -> None:
    doc = _parse_cv(CV_MD)
    edu_seg = next(s for s in doc.segments if s.segment_type == "education")
    for line in edu_seg.display_lines:
        assert ":::" not in line


def test_cv_skills_paragraph_parsed() -> None:
    doc = _parse_cv(CV_MD)
    para_segs = [s for s in doc.segments if s.segment_type == "paragraph"]
    all_text = " ".join(s.raw_text for s in para_segs)
    assert "Programming" in all_text or "Python" in all_text


def test_cv_line_indices_are_contiguous() -> None:
    doc = _parse_cv(CV_MD)
    expected_line = 0
    for seg in doc.segments:
        assert seg.line_start == expected_line, (
            f"segment {seg.segment_id}: expected line_start={expected_line}, "
            f"got {seg.line_start}"
        )
        expected_line = seg.line_end + 1


def test_cv_all_lines_length_matches_segments() -> None:
    doc = _parse_cv(CV_MD)
    total_from_segments = sum(len(s.display_lines) for s in doc.segments)
    assert len(doc.all_lines) == total_from_segments


# ---------------------------------------------------------------------------
# Letter / email parsing
# ---------------------------------------------------------------------------


def test_letter_splits_into_paragraphs() -> None:
    doc = _parse_paragraphs("letter", LETTER_MD)
    assert len(doc.segments) == 3
    assert all(s.segment_type == "paragraph" for s in doc.segments)


def test_letter_segment_ids_use_doc_type() -> None:
    doc = _parse_paragraphs("letter", LETTER_MD)
    assert all(s.segment_id.startswith("letter:") for s in doc.segments)


def test_letter_line_indices_contiguous() -> None:
    doc = _parse_paragraphs("letter", LETTER_MD)
    expected = 0
    for seg in doc.segments:
        assert seg.line_start == expected
        expected = seg.line_end + 1


def test_email_parsed_separately() -> None:
    doc = _parse_paragraphs("email", "Short email body.\n\nBest regards.")
    assert len(doc.segments) == 2
    assert doc.segments[0].segment_id == "email:paragraph:0"
    assert doc.segments[1].segment_id == "email:paragraph:1"


# ---------------------------------------------------------------------------
# ParsedDocument helpers
# ---------------------------------------------------------------------------


def test_segment_for_line_returns_correct_segment() -> None:
    doc = _parse_cv(CV_MD)
    for seg in doc.segments:
        for line_idx in range(seg.line_start, seg.line_end + 1):
            found = doc.segment_for_line(line_idx)
            assert found is not None
            assert found.segment_id == seg.segment_id


def test_segment_for_line_returns_none_out_of_range() -> None:
    doc = _parse_paragraphs("letter", LETTER_MD)
    assert doc.segment_for_line(-1) is None
    assert doc.segment_for_line(9999) is None


def test_segments_in_range_single_segment() -> None:
    doc = _parse_paragraphs("letter", LETTER_MD)
    seg = doc.segments[0]
    result = doc.segments_in_range(seg.line_start, seg.line_end)
    assert seg in result


def test_segments_in_range_spans_multiple() -> None:
    doc = _parse_paragraphs("letter", LETTER_MD)
    first = doc.segments[0]
    last = doc.segments[-1]
    result = doc.segments_in_range(first.line_start, last.line_end)
    assert len(result) == len(doc.segments)


def test_segments_in_range_inverted_start_end() -> None:
    """Range (end, start) should behave the same as (start, end)."""
    doc = _parse_paragraphs("letter", LETTER_MD)
    first = doc.segments[0]
    second = doc.segments[1]
    result_a = doc.segments_in_range(first.line_start, second.line_end)
    result_b = doc.segments_in_range(second.line_end, first.line_start)
    assert result_a == result_b
