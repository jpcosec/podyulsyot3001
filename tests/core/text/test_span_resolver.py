"""Tests for span_resolver module."""

import pytest

from src.core.text.span_resolver import resolve_span, SpanResolution


class TestExactMatchFound:
    def test_simple_exact_match(self):
        source = "The quick brown fox jumps over the lazy dog."
        result = resolve_span(source, "quick brown fox")
        assert result.found is True
        assert result.exact_quote == "quick brown fox"
        assert result.start_line == 1
        assert result.end_line == 1

    def test_exact_match_unicode(self):
        source = "Café résumé naïve"
        result = resolve_span(source, "Café résumé naïve")
        assert result.found is True
        assert result.exact_quote == "Café résumé naïve"


class TestCaseInsensitive:
    def test_case_insensitive_match(self):
        source = "The Quick Brown Fox"
        result = resolve_span(source, "quick brown fox")
        assert result.found is True
        assert result.exact_quote == "Quick Brown Fox"


class TestWhitespaceNormalization:
    def test_whitespace_collapsed(self):
        source = "Hello   world"
        result = resolve_span(source, "Hello  world")
        assert result.found is True

    def test_leading_trailing_whitespace(self):
        source = "  Hello world  "
        result = resolve_span(source, "Hello world")
        assert result.found is True

    def test_tabs_and_newlines(self):
        source = "Hello\t\tworld\n\tnice"
        result = resolve_span(source, "Hello  world")
        assert result.found is True


class TestNotFound:
    def test_quote_not_in_source(self):
        source = "The quick brown fox"
        result = resolve_span(source, "not found")
        assert result.found is False
        assert result.start_line is None

    def test_partial_match_not_found(self):
        source = "Hello world"
        result = resolve_span(source, "worlds")
        assert result.found is False


class TestMultilineSource:
    def test_match_in_middle_of_multiline(self):
        source = "Line one\nLine two\nLine three"
        result = resolve_span(source, "Line two")
        assert result.found is True
        assert result.start_line == 2
        assert result.end_line == 2

    def test_match_across_lines(self):
        source = "Line one\ncontinues here"
        result = resolve_span(source, "one continues")
        assert result.found is True
        assert result.start_line == 1
        assert result.end_line == 2


class TestMatchAtBoundaries:
    def test_match_at_start(self):
        source = "Start of text"
        result = resolve_span(source, "Start")
        assert result.found is True
        assert result.start_line == 1
        assert result.start_offset == 0

    def test_match_at_end(self):
        source = "End of text"
        result = resolve_span(source, "text")
        assert result.found is True
        assert result.end_line == 1
        assert result.end_offset == len(source)


class TestEmptyQuote:
    def test_none_quote(self):
        source = "Some text"
        result = resolve_span(source, None)
        assert result.found is False

    def test_empty_quote(self):
        source = "Some text"
        result = resolve_span(source, "")
        assert result.found is False

    def test_whitespace_only_quote(self):
        source = "Some text"
        result = resolve_span(source, "   ")
        assert result.found is False


class TestOverlappingMatches:
    def test_first_match_used(self):
        source = "foo bar foo baz"
        result = resolve_span(source, "foo")
        assert result.found is True
        assert result.start_offset == 0


class TestMixedLineEndings:
    def test_crlf_line_endings(self):
        source = "Line one\r\nLine two\r\nLine three"
        result = resolve_span(source, "Line two")
        assert result.found is True
        assert result.start_line == 2

    def test_mixed_crlf_lf(self):
        source = "Line one\nLine two\r\nLine three"
        result = resolve_span(source, "Line two")
        assert result.found is True
        assert result.start_line == 2


class TestPreviewSnippet:
    def test_preview_has_context(self):
        source = "A" * 50 + "MATCH" + "B" * 50
        result = resolve_span(source, "MATCH")
        assert result.found is True
        assert result.preview_snippet is not None
        assert "MATCH" in result.preview_snippet

    def test_preview_at_start_short_context(self):
        source = "SHORT"
        result = resolve_span(source, "SHORT")
        assert result.found is True
        assert result.preview_snippet is None

    def test_preview_with_ellipsis(self):
        source = "A" * 50 + "MATCH" + "B" * 50
        result = resolve_span(source, "MATCH")
        snippet = result.preview_snippet
        assert snippet is not None
        assert "..." in snippet or len(snippet) < len(source)
