"""Document strategy definitions and selection logic for generate_documents_v2."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocumentStrategy:
    """Rules that shape document structure for a given market or context.

    ``section_order``
        Preferred CV section ordering.  Sections not listed come after in their
        original order.
    ``include_photo``
        Whether a photo is expected by convention (e.g. Germany: True).
    ``formal_salutation``
        Letter uses formal address (e.g. "Sehr geehrte Damen und Herren").
    ``date_format``
        strftime pattern for dates in the document (e.g. ``"%d.%m.%Y"``).
    ``notes``
        Human-readable description for audit logs and UI display.
    """

    name: str
    section_order: list[str] = field(default_factory=list)
    include_photo: bool = False
    formal_salutation: bool = False
    date_format: str = "%B %d, %Y"
    notes: str = ""


STRATEGY_GENERIC = DocumentStrategy(
    name="generic",
    section_order=["summary", "experience", "education", "skills"],
    include_photo=False,
    formal_salutation=False,
    date_format="%B %d, %Y",
    notes="Sensible international defaults — no region-specific conventions applied.",
)

STRATEGY_GERMAN_PROFESSIONAL = DocumentStrategy(
    name="german_professional",
    section_order=[
        "persoenliche_daten",
        "berufserfahrung",
        "ausbildung",
        "kenntnisse",
        "sprachen",
        "summary",
        "experience",
        "education",
        "skills",
    ],
    include_photo=True,
    formal_salutation=True,
    date_format="%d.%m.%Y",
    notes=(
        "German professional market conventions: DIN-style section order, "
        "photo expected, formal salutation, day-first date format."
    ),
)

STRATEGY_ACADEMIC = DocumentStrategy(
    name="academic",
    section_order=[
        "publications",
        "research",
        "teaching",
        "summary",
        "experience",
        "education",
        "skills",
    ],
    include_photo=False,
    formal_salutation=True,
    date_format="%B %Y",
    notes="Academic variant: publications and research sections prioritized.",
)

_STRATEGY_MAP: dict[str, DocumentStrategy] = {
    s.name: s
    for s in (STRATEGY_GENERIC, STRATEGY_GERMAN_PROFESSIONAL, STRATEGY_ACADEMIC)
}


def select_strategy(
    strategy_type: str | None,
    target_language: str | None,
) -> DocumentStrategy:
    """Return the appropriate DocumentStrategy.

    Selection priority:
    1. Explicit ``strategy_type`` name if provided and recognized.
    2. Language-based default: ``"de"`` -> ``STRATEGY_GERMAN_PROFESSIONAL``.
    3. Fallback: ``STRATEGY_GENERIC``.

    Args:
        strategy_type: Optional strategy name (e.g. ``"academic"``).
        target_language: BCP-47 language tag (e.g. ``"de"``).

    Returns:
        The resolved DocumentStrategy.
    """
    if strategy_type:
        return _STRATEGY_MAP.get(strategy_type, STRATEGY_GENERIC)
    if target_language and target_language.lower().startswith("de"):
        return STRATEGY_GERMAN_PROFESSIONAL
    return STRATEGY_GENERIC
