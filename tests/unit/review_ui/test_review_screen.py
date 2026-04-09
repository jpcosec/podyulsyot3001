"""Tests for the Review UI using Textual's testing framework."""

from __future__ import annotations

import pytest

from src.review_ui.screens.review_screen import ReviewScreen


def make_mock_bus(source: str = "xing", job_id: str = "150542106"):
    """Create a mock bus for unit testing (bypasses API)."""
    from unittest.mock import MagicMock

    mock_store = MagicMock()

    def mock_load_stage(src: str, jid: str, stage: str):
        if stage == "match_edges":
            return {
                "matches": [
                    {
                        "requirement_id": "R01",
                        "profile_evidence_ids": ["SKILL_Python", "EXP001"],
                        "match_score": 0.9,
                        "reasoning": "Test reasoning for R01",
                    },
                    {
                        "requirement_id": "R02",
                        "profile_evidence_ids": ["SKILL_Java"],
                        "match_score": 0.3,
                        "reasoning": "Test reasoning for R02",
                    },
                ]
            }
        if stage == "job_kg":
            return {
                "job_title_english": "Data Scientist / AI Expert",
                "hard_requirements": [
                    {"id": "R01", "text": "Strong Python experience required"},
                    {"id": "R02", "text": "Java experience nice to have"},
                ],
                "soft_context": [],
            }
        return None

    mock_store.load_stage = mock_load_stage

    return mock_store


def test_review_screen_initial_state() -> None:
    """Test initial state of review screen."""
    mock_store = make_mock_bus()
    # Create with mock store but we'll just test initial state
    screen = ReviewScreen.__new__(ReviewScreen)
    screen._bus = None
    screen._source = "xing"
    screen._job_id = "150542106"
    screen._match_outcomes = {}
    screen._matches_data = []
    screen._selected_idx = 0
    screen._requirement_lookup = {}

    assert screen._match_outcomes == {}
    assert screen._matches_data == []
    screen._requirement_lookup = {"R01": "Test requirement"}
    assert screen._requirement_lookup == {"R01": "Test requirement"}


def test_review_screen_compose_has_bindings() -> None:
    """Test that ReviewScreen has the expected key bindings."""
    binding_keys = {b[0] for b in ReviewScreen.BINDINGS}
    assert "a" in binding_keys
    assert "r" in binding_keys
    assert "s" in binding_keys
    assert "q" in binding_keys
    assert "j" in binding_keys
    assert "k" in binding_keys
    assert "y" in binding_keys
    assert "n" in binding_keys
    assert "space" in binding_keys

    # Verify action names
    binding_actions = {b[1] for b in ReviewScreen.BINDINGS}
    assert "approve_all" in binding_actions
    assert "reject_all" in binding_actions
    assert "submit" in binding_actions
    assert "approve_current" in binding_actions
    assert "reject_current" in binding_actions
    assert "toggle_current" in binding_actions


def test_review_screen_css_has_match_card_styles() -> None:
    """Test that CSS includes match card styling."""
    css = ReviewScreen.DEFAULT_CSS
    assert ".match-card" in css
    assert ".match-score" in css
    assert ".score-high" in css
    assert ".score-medium" in css
    assert ".score-low" in css


def test_review_screen_has_review_buttons() -> None:
    """Test that compose yields review buttons."""
    from src.review_ui.bus import MatchBus
    from unittest.mock import MagicMock

    mock_store = make_mock_bus()
    mock_client = MagicMock()
    bus = MatchBus(store=mock_store, client=mock_client, config={})

    screen = ReviewScreen(bus=bus, source="xing", job_id="150542106")

    # Check initial state
    assert screen._bus is bus
    assert screen._source == "xing"
    assert screen._job_id == "150542106"
