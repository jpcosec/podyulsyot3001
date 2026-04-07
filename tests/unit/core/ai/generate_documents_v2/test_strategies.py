"""Tests for the regional document strategy layer."""

from __future__ import annotations

import pytest

from src.core.ai.generate_documents_v2.contracts.profile import SectionMappingItem
from src.core.ai.generate_documents_v2.profile_loader import filter_sections_by_strategy
from src.core.ai.generate_documents_v2.strategies import (
    STRATEGY_ACADEMIC,
    STRATEGY_GENERIC,
    STRATEGY_GERMAN_PROFESSIONAL,
    DocumentStrategy,
    select_strategy,
)


# ---------------------------------------------------------------------------
# select_strategy
# ---------------------------------------------------------------------------


def test_explicit_strategy_type_takes_priority():
    assert select_strategy("academic", "de") is STRATEGY_ACADEMIC


def test_explicit_german_professional_name():
    assert select_strategy("german_professional", None) is STRATEGY_GERMAN_PROFESSIONAL


def test_explicit_generic_name():
    assert select_strategy("generic", "de") is STRATEGY_GENERIC


def test_unknown_strategy_type_falls_back_to_generic():
    assert select_strategy("unknown_xyz", None) is STRATEGY_GENERIC


def test_language_de_defaults_to_german_professional():
    assert select_strategy(None, "de") is STRATEGY_GERMAN_PROFESSIONAL


def test_language_de_de_variant_defaults_to_german_professional():
    assert select_strategy(None, "de-DE") is STRATEGY_GERMAN_PROFESSIONAL


def test_language_en_defaults_to_generic():
    assert select_strategy(None, "en") is STRATEGY_GENERIC


def test_no_inputs_defaults_to_generic():
    assert select_strategy(None, None) is STRATEGY_GENERIC


def test_strategy_constants_have_distinct_names():
    names = {STRATEGY_GENERIC.name, STRATEGY_GERMAN_PROFESSIONAL.name, STRATEGY_ACADEMIC.name}
    assert len(names) == 3


def test_german_professional_has_formal_salutation():
    assert STRATEGY_GERMAN_PROFESSIONAL.formal_salutation is True


def test_german_professional_day_first_date_format():
    import datetime
    d = datetime.date(2025, 1, 15)
    assert d.strftime(STRATEGY_GERMAN_PROFESSIONAL.date_format) == "15.01.2025"


def test_academic_prioritizes_publications():
    first = STRATEGY_ACADEMIC.section_order[0]
    assert first == "publications"


# ---------------------------------------------------------------------------
# filter_sections_by_strategy
# ---------------------------------------------------------------------------


def _make_item(section_id: str, country_context: str = "global") -> SectionMappingItem:
    return SectionMappingItem(
        section_id=section_id,
        target_document="cv",
        country_context=country_context,
    )


def test_global_items_always_included():
    items = [_make_item("summary", "global")]
    result = filter_sections_by_strategy(items, STRATEGY_GENERIC)
    assert len(result) == 1
    assert result[0].section_id == "summary"


def test_matching_country_context_included():
    items = [_make_item("berufserfahrung", "german_professional")]
    result = filter_sections_by_strategy(items, STRATEGY_GERMAN_PROFESSIONAL)
    assert len(result) == 1


def test_non_matching_country_context_excluded():
    items = [_make_item("berufserfahrung", "german_professional")]
    result = filter_sections_by_strategy(items, STRATEGY_GENERIC)
    assert result == []


def test_section_order_applied():
    items = [
        _make_item("skills", "global"),
        _make_item("summary", "global"),
        _make_item("experience", "global"),
    ]
    strategy = DocumentStrategy(
        name="test",
        section_order=["summary", "experience", "skills"],
    )
    result = filter_sections_by_strategy(items, strategy)
    assert [i.section_id for i in result] == ["summary", "experience", "skills"]


def test_items_not_in_order_come_last():
    items = [
        _make_item("extra", "global"),
        _make_item("summary", "global"),
    ]
    strategy = DocumentStrategy(name="test", section_order=["summary"])
    result = filter_sections_by_strategy(items, strategy)
    assert result[0].section_id == "summary"
    assert result[1].section_id == "extra"


def test_empty_input_returns_empty():
    result = filter_sections_by_strategy([], STRATEGY_GENERIC)
    assert result == []


def test_mixed_contexts_for_german_strategy():
    items = [
        _make_item("summary", "global"),
        _make_item("berufserfahrung", "german_professional"),
        _make_item("publications", "academic"),
    ]
    result = filter_sections_by_strategy(items, STRATEGY_GERMAN_PROFESSIONAL)
    section_ids = {i.section_id for i in result}
    assert "summary" in section_ids
    assert "berufserfahrung" in section_ids
    assert "publications" not in section_ids
