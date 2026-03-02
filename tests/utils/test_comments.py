"""Tests for comment extraction and logging system."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from src.utils.comments import (
    InlineComment,
    CommentLogEntry,
    extract_comments,
    extract_comments_from_files,
    load_comment_log,
    append_to_comment_log,
    format_comments_for_prompt,
)


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestExtractSingleComment:
    """Test extraction of single comments."""
    
    def test_extract_single_comment(self, temp_dir):
        """Extract one comment from a file."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Line 1\n<!-- This is a comment -->\nLine 3")
        
        comments = extract_comments(test_file)
        
        assert len(comments) == 1
        assert comments[0].text == "This is a comment"
        assert comments[0].line == 2
        assert comments[0].context == "<!-- This is a comment -->"
    
    def test_extract_comment_with_whitespace(self, temp_dir):
        """Comments with extra whitespace are stripped."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Line 1\n<!--   spaces around   -->\nLine 3")
        
        comments = extract_comments(test_file)
        
        assert len(comments) == 1
        assert comments[0].text == "spaces around"


class TestExtractMultilineComment:
    """Test extraction of multiline comments."""
    
    def test_extract_multiline_comment(self, temp_dir):
        """Extract comment spanning multiple lines."""
        test_file = temp_dir / "test.md"
        content = """Line 1
<!--
This is a multiline
comment with several lines
of text
-->
Line 6"""
        test_file.write_text(content)
        
        comments = extract_comments(test_file)
        
        assert len(comments) == 1
        # Line number should be the line where comment starts
        assert comments[0].line == 2
        # Text should preserve newlines in the comment content
        assert "This is a multiline" in comments[0].text
        assert "comment with several lines" in comments[0].text
        assert "of text" in comments[0].text


class TestExtractMultipleComments:
    """Test extraction of multiple comments with correct line numbers."""
    
    def test_extract_multiple_comments(self, temp_dir):
        """Extract several comments with correct line numbers."""
        test_file = temp_dir / "test.md"
        content = """Line 1
<!-- comment 1 -->
Line 3
<!-- comment 2 -->
Line 5
<!-- comment 3 -->
Line 7"""
        test_file.write_text(content)
        
        comments = extract_comments(test_file)
        
        assert len(comments) == 3
        assert comments[0].text == "comment 1"
        assert comments[0].line == 2
        assert comments[1].text == "comment 2"
        assert comments[1].line == 4
        assert comments[2].text == "comment 3"
        assert comments[2].line == 6


class TestExtractNoComments:
    """Test files with no comments."""
    
    def test_extract_no_comments(self, temp_dir):
        """File with no comments returns empty list."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Line 1\nLine 2\nLine 3")
        
        comments = extract_comments(test_file)
        
        assert comments == []
    
    def test_extract_nonexistent_file(self, temp_dir):
        """Nonexistent file returns empty list."""
        test_file = temp_dir / "nonexistent.md"
        
        comments = extract_comments(test_file)
        
        assert comments == []


class TestContextCaptured:
    """Test that surrounding line context is captured."""
    
    def test_context_captured(self, temp_dir):
        """Surrounding line is captured as context."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Line 1\nSome content here <!-- comment -->\nLine 3")
        
        comments = extract_comments(test_file)
        
        assert len(comments) == 1
        assert comments[0].context == "Some content here <!-- comment -->"
    
    def test_context_empty_line(self, temp_dir):
        """Comment on empty line has empty context."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Line 1\n<!-- comment -->\nLine 3")
        
        comments = extract_comments(test_file)
        
        # The context line itself contains the comment
        assert "comment" in comments[0].context


class TestRelativePaths:
    """Test file path handling with and without job_dir."""
    
    def test_relative_paths_with_job_dir(self, temp_dir):
        """File paths are relative to job_dir when provided."""
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        test_file = job_dir / "planning" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Line 1\n<!-- comment -->\nLine 3")
        
        comments = extract_comments(test_file, job_dir=job_dir)
        
        assert len(comments) == 1
        assert comments[0].file == "planning/test.md"
    
    def test_absolute_paths_without_job_dir(self, temp_dir):
        """Absolute paths used when job_dir not provided."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Line 1\n<!-- comment -->\nLine 3")
        
        comments = extract_comments(test_file, job_dir=None)
        
        assert len(comments) == 1
        assert str(test_file) in comments[0].file
    
    def test_path_not_relative_to_job_dir(self, temp_dir):
        """Falls back to absolute path if file not relative to job_dir."""
        job_dir = temp_dir / "job1"
        job_dir.mkdir()
        test_file = temp_dir / "other" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Line 1\n<!-- comment -->\nLine 3")
        
        comments = extract_comments(test_file, job_dir=job_dir)
        
        # Should use absolute path as fallback
        assert str(test_file) in comments[0].file


class TestExtractFromMultipleFiles:
    """Test batch extraction from multiple files."""
    
    def test_extract_comments_from_files(self, temp_dir):
        """Extract comments from multiple files."""
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        
        file1 = job_dir / "file1.md"
        file1.write_text("Line 1\n<!-- comment1 -->\nLine 3")
        
        file2 = job_dir / "file2.md"
        file2.write_text("Line 1\n<!-- comment2 -->\nLine 3")
        
        comments = extract_comments_from_files([file1, file2], job_dir)
        
        assert len(comments) == 2
        assert comments[0].text == "comment1"
        assert comments[0].file == "file1.md"
        assert comments[1].text == "comment2"
        assert comments[1].file == "file2.md"
    
    def test_extract_from_empty_list(self, temp_dir):
        """Empty file list returns empty comments."""
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        
        comments = extract_comments_from_files([], job_dir)
        
        assert comments == []


class TestCommentLogAppend:
    """Test appending entries to comment log."""
    
    def test_comment_log_append(self, temp_dir):
        """Append entries to comment log with correct structure."""
        log_path = temp_dir / "comments.log.json"
        
        comments = [
            InlineComment("file1.md", 42, "test comment", "some context"),
        ]
        
        append_to_comment_log(log_path, "test_step", comments)
        
        # Verify file was created
        assert log_path.exists()
        
        # Load and verify structure
        data = json.loads(log_path.read_text())
        assert len(data) == 1
        assert data[0]["step"] == "test_step"
        assert "run_at" in data[0]
        assert len(data[0]["comments"]) == 1
        assert data[0]["comments"][0]["text"] == "test comment"
    
    def test_log_entry_timestamp(self, temp_dir):
        """Timestamp is valid ISO 8601 and recent."""
        log_path = temp_dir / "comments.log.json"
        
        before = datetime.now(timezone.utc).isoformat()
        append_to_comment_log(log_path, "step1", [])
        after = datetime.now(timezone.utc).isoformat()
        
        data = json.loads(log_path.read_text())
        timestamp = data[0]["run_at"]
        
        # Should be ISO format string
        assert "T" in timestamp
        # Should be between before and after
        assert before <= timestamp <= after


class TestCommentLogAccumulates:
    """Test that multiple appends accumulate without overwriting."""
    
    def test_comment_log_accumulates(self, temp_dir):
        """Multiple appends don't overwrite previous entries."""
        log_path = temp_dir / "comments.log.json"
        
        # First append
        comments1 = [InlineComment("file1.md", 10, "comment1", "ctx1")]
        append_to_comment_log(log_path, "step1", comments1)
        
        # Second append
        comments2 = [InlineComment("file2.md", 20, "comment2", "ctx2")]
        append_to_comment_log(log_path, "step2", comments2)
        
        # Verify both entries exist
        data = json.loads(log_path.read_text())
        assert len(data) == 2
        assert data[0]["step"] == "step1"
        assert data[1]["step"] == "step2"


class TestLoadCommentLog:
    """Test loading comment log from file."""
    
    def test_load_comment_log_missing_file(self, temp_dir):
        """Missing log file returns empty list."""
        log_path = temp_dir / "nonexistent.log.json"
        
        entries = load_comment_log(log_path)
        
        assert entries == []
    
    def test_load_comment_log_from_file(self, temp_dir):
        """Load previously saved comment log."""
        log_path = temp_dir / "comments.log.json"
        
        # Create log
        comments = [InlineComment("file.md", 5, "comment text", "context")]
        append_to_comment_log(log_path, "my_step", comments)
        
        # Load it back
        entries = load_comment_log(log_path)
        
        assert len(entries) == 1
        assert entries[0].step == "my_step"
        assert len(entries[0].comments) == 1
        assert entries[0].comments[0]["text"] == "comment text"
    
    def test_load_comment_log_invalid_json(self, temp_dir):
        """Invalid JSON gracefully returns empty list."""
        log_path = temp_dir / "bad.log.json"
        log_path.write_text("{ invalid json }")
        
        entries = load_comment_log(log_path)
        
        assert entries == []


class TestFormatCommentsForPrompt:
    """Test formatting comments for LLM injection."""
    
    def test_format_for_prompt(self, temp_dir):
        """Format comments as human-readable text block."""
        comments = [
            InlineComment("planning/match.md", 42, "this is about wet lab", "- Requirement: Laboratory"),
            InlineComment("planning/match.md", 58, "add more publications", "## Skills"),
        ]
        
        formatted = format_comments_for_prompt(comments)
        
        # Should contain header
        assert "User Comments:" in formatted
        
        # Should contain file/line info
        assert "planning/match.md" in formatted
        assert "line 42" in formatted
        assert "line 58" in formatted
        
        # Should contain comment texts
        assert "this is about wet lab" in formatted
        assert "add more publications" in formatted
        
        # Should contain context
        assert "Laboratory" in formatted
        assert "Skills" in formatted
    
    def test_format_for_prompt_empty(self):
        """Empty comments returns empty string."""
        formatted = format_comments_for_prompt([])
        
        assert formatted == ""
    
    def test_format_for_prompt_single(self):
        """Format single comment correctly."""
        comments = [
            InlineComment("file.md", 10, "test", "line content"),
        ]
        
        formatted = format_comments_for_prompt(comments)
        
        assert "User Comments:" in formatted
        assert "file.md" in formatted
        assert '"test"' in formatted
