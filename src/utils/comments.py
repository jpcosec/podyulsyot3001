"""Comment extraction and logging system for iterative feedback.

Extracts inline HTML comments (<!-- ... -->) from markdown files,
logs them with timestamps and step identifiers, and formats them for
LLM prompt injection.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import re
import json
from datetime import datetime, timezone


COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)


@dataclass
class InlineComment:
    """A single inline comment extracted from a file."""
    file: str       # relative path within job dir (or absolute if no job_dir)
    line: int       # 1-based line number
    text: str       # comment content (stripped of <!-- -->)
    context: str    # the line containing or surrounding the comment


def extract_comments(file_path: Path, job_dir: Path | None = None) -> list[InlineComment]:
    """Extract all <!-- ... --> comments from a file.
    
    Args:
        file_path: Path to the file to extract comments from.
        job_dir: Optional job directory. If provided, file paths in returned
                 InlineComment objects will be relative to this directory.
                 Otherwise, absolute paths are used.
    
    Returns:
        List of InlineComment objects.
    """
    if not file_path.exists():
        return []
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []
    
    lines = content.split("\n")
    comments = []
    
    # Find all matches with their positions in the original text
    for match in COMMENT_RE.finditer(content):
        comment_text = match.group(1).strip()
        
        # Find line number by counting newlines up to match start
        line_num = content[:match.start()].count("\n") + 1
        
        # Get context: the line containing the comment
        if line_num - 1 < len(lines):
            context = lines[line_num - 1].strip()
        else:
            context = ""
        
        # Determine file path (relative or absolute)
        if job_dir:
            try:
                file_rel = file_path.relative_to(job_dir)
                file_str = str(file_rel)
            except ValueError:
                # file_path not relative to job_dir, use absolute
                file_str = str(file_path)
        else:
            file_str = str(file_path)
        
        comments.append(InlineComment(
            file=file_str,
            line=line_num,
            text=comment_text,
            context=context,
        ))
    
    return comments


def extract_comments_from_files(
    paths: list[Path],
    job_dir: Path,
) -> list[InlineComment]:
    """Extract comments from multiple files.
    
    Args:
        paths: List of file paths to extract comments from.
        job_dir: Job directory for relative path calculation.
    
    Returns:
        Accumulated list of InlineComment objects from all files.
    """
    all_comments = []
    for path in paths:
        all_comments.extend(extract_comments(path, job_dir=job_dir))
    return all_comments


@dataclass
class CommentLogEntry:
    """A single entry in the comment log (one step run)."""
    step: str
    run_at: str  # ISO 8601
    comments: list[dict]


def load_comment_log(log_path: Path) -> list[CommentLogEntry]:
    """Load comment log from JSON file.
    
    Args:
        log_path: Path to the comment log JSON file.
    
    Returns:
        List of CommentLogEntry objects. Returns empty list if file
        doesn't exist or JSON parsing fails.
    """
    if not log_path.exists():
        return []
    
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        return [CommentLogEntry(**entry) for entry in data]
    except Exception:
        # JSON parse error or other issue — return empty list
        return []


def append_to_comment_log(
    log_path: Path,
    step: str,
    comments: list[InlineComment],
) -> None:
    """Append a new entry to the comment log JSON file.
    
    Args:
        log_path: Path to the comment log JSON file.
        step: Name of the step being logged.
        comments: List of InlineComment objects to log.
    """
    # Load existing log or start fresh
    entries = load_comment_log(log_path)
    
    # Create new entry
    now = datetime.now(timezone.utc).isoformat()
    new_entry = CommentLogEntry(
        step=step,
        run_at=now,
        comments=[asdict(c) for c in comments],
    )
    
    # Append to list
    entries.append(new_entry)
    
    # Create parent directories if needed
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write back to file
    json_data = [asdict(entry) for entry in entries]
    log_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def format_comments_for_prompt(comments: list[InlineComment]) -> str:
    """Format comments as a text block suitable for LLM prompt injection.
    
    Args:
        comments: List of InlineComment objects.
    
    Returns:
        Human-readable formatted text block. Returns empty string if
        comments list is empty.
    """
    if not comments:
        return ""
    
    lines = ["User Comments:\n"]
    
    for comment in comments:
        lines.append(f"[file: {comment.file}, line {comment.line}]")
        lines.append(f'"{comment.text}"')
        lines.append(f'Context: "{comment.context}"\n')
    
    return "\n".join(lines)
