"""URLNode — URL pattern that identifies a logical page in a portal.

A URLNode is a coarse identity by URL shape, not by content.
Multiple RoomStates can share one URLNode (e.g. home.anon, home.with_modal).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs


@dataclass
class URLNode:
    """
    id:           semantic name, e.g. "home", "job_detail", "search_results"
    url_template: human-readable pattern, e.g. "https://stepstone.de/jobs/in-{city}{?page,sort}"
    _pattern:     compiled regex derived from the template (auto-built)
    """

    id: str
    url_template: str
    _pattern: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._pattern = _compile_pattern(self.url_template)

    def match(self, raw_url: str) -> bool:
        parsed = urlparse(raw_url)
        candidate = (parsed.netloc + parsed.path).rstrip("/")
        return bool(self._pattern.match(candidate))

    def extract_params(self, raw_url: str) -> dict[str, str]:
        parsed = urlparse(raw_url)
        netloc_path = (parsed.netloc + parsed.path).rstrip("/")
        m = self._pattern.match(netloc_path)
        path_params = m.groupdict() if m else {}
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        return {**path_params, **query_params}

    def to_dict(self) -> dict:
        return {"id": self.id, "url_template": self.url_template}

    @classmethod
    def from_dict(cls, data: dict) -> "URLNode":
        return cls(id=data["id"], url_template=data["url_template"])


def _compile_pattern(template: str) -> re.Pattern:
    """Convert a URL template into a regex.

    {city}       → named capture group (?P<city>[^/?]+)
    {?page,sort} → optional query params (stripped before matching path)
    """
    # Strip optional query param block {?...} — handled separately via parse_qs
    path_template = re.sub(r"\{\?[^}]+\}", "", template)
    # Keep netloc + path for domain-aware matching
    parsed = urlparse(path_template)
    netloc_path = (parsed.netloc + parsed.path).rstrip("/") or "/"
    # Replace {param} with named capture groups
    pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/?]+)", re.escape(netloc_path).replace(r"\{", "{").replace(r"\}", "}"))
    return re.compile(f"^{pattern}$")
