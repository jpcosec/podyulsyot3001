from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourcePolicy:
    source_key: str
    allowed_domains: tuple[str, ...] = field(default_factory=tuple)
    supports_apply: bool = False
    manual_approval_required: bool = True
