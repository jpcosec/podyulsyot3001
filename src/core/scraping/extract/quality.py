from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QualityCheckResult:
    is_acceptable: bool
    warnings: list[str] = field(default_factory=list)


def check_text_quality(text: str, min_length: int = 300) -> QualityCheckResult:
    warnings: list[str] = []
    if len(text) < min_length:
        warnings.append("text_too_short")
    if "cookie" in text.lower() and len(text) < 1000:
        warnings.append("likely_cookie_wall")
    return QualityCheckResult(is_acceptable=not warnings, warnings=warnings)
