from __future__ import annotations

import html
import re

SCRIPT_PATTERN = re.compile(r"(?is)<script.*?>.*?</script>")
STYLE_PATTERN = re.compile(r"(?is)<style.*?>.*?</style>")
TAG_PATTERN = re.compile(r"<[^>]+>")
MULTISPACE_PATTERN = re.compile(r"[ \t]+")
MULTINEWLINE_PATTERN = re.compile(r"\n{3,}")


def extract_text(raw_html: str) -> str:
    without_scripts = SCRIPT_PATTERN.sub(" ", raw_html)
    without_styles = STYLE_PATTERN.sub(" ", without_scripts)
    text = TAG_PATTERN.sub(" ", without_styles)
    text = html.unescape(text)
    text = text.replace("\r", "\n")
    text = MULTISPACE_PATTERN.sub(" ", text)
    normalized = MULTINEWLINE_PATTERN.sub("\n\n", text)
    return normalized.strip()
