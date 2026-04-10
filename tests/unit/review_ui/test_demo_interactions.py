"""Interaction tests for the HITL Review UI screens using Textual's Pilot."""

from __future__ import annotations

import pytest
from textual.widgets import Button, ListItem, ListView, Label, Static, TextArea
from src.review_ui.demo import DemoLauncher, DemoBus
from src.review_ui.app import MatchReviewApp
from src.review_ui.screens.match_review_screen import MatchReviewScreen
from src.review_ui.screens.blueprint_review_screen import BlueprintReviewScreen, IntentEditModal
from src.review_ui.screens.content_review_screen import ContentReviewScreen, DocEditor, EditorMode, AnnotationModal
from src.review_ui.screens.profile_diff_screen import ProfileDiffScreen


@pytest.mark.asyncio
async def test_demo_launcher_flow() -> None:
    """Test that the launcher correctly returns the configured app."""
    app = DemoLauncher()
    async with app.run_test() as pilot:
        # Check initial menu
        assert app.query_one("#btn_1").display is True
        
        # Click button 1
        await pilot.click("#btn_1")
        # The app should exit with a MatchReviewApp instance
        assert isinstance(app.return_value, MatchReviewApp)
        assert app.return_value._bus.demo_stage == "hitl_1_match_evidence"


@pytest.mark.asyncio
async def test_match_review_interaction() -> None:
    """Test keyboard and button interactions in MatchReviewScreen."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="job_123")
    
    async with app.run_test() as pilot:
        # Wait for data to load and screen to be pushed
        await pilot.pause(1.0)
        
        screen = app.screen
        assert isinstance(screen, MatchReviewScreen)
        list_view = screen.query_one(ListView)
        
        # Verify initial selection
        assert list_view.index == 0
        
        # Press 'n' to reject first requirement
        await pilot.press("n")
        assert screen._outcomes["R01"] == "reject"
        assert list_view.index == 1 # Auto-advanced
        
        # Press 'y' to approve second requirement
        await pilot.press("y")
        assert screen._outcomes["R02"] == "approve"
        assert list_view.index == 2
        
        # Press 'a' to approve all
        await pilot.press("a")
        assert all(o == "approve" for o in screen._outcomes.values())
        
        # Check summary update
        summary = screen.query_one("#summary-bar", Label)
        assert "✓ 3" in str(summary.render())


@pytest.mark.asyncio
async def test_blueprint_review_interaction() -> None:
    """Test modal editing in BlueprintReviewScreen."""
    bus = DemoBus("hitl_2_blueprint_logic")
    app = MatchReviewApp(bus=bus, source="demo", job_id="job_123")
    
    async with app.run_test() as pilot:
        await pilot.pause(1.0)
        screen = app.screen
        assert isinstance(screen, BlueprintReviewScreen)
        
        # Press 'e' to edit intent of first section
        await pilot.press("e")
        
        # Verify modal is pushed
        await pilot.pause(0.2)
        assert isinstance(app.screen, IntentEditModal)
        
        # Clear and type new intent
        modal = app.screen
        modal.query_one("#intent-input").value = ""
        await pilot.press(*"New Intent")
        await pilot.click("#btn-save")
        
        # Verify it's back on the main screen and data is updated
        await pilot.pause(0.2)
        assert isinstance(app.screen, BlueprintReviewScreen)
        assert screen._modified_sections[0]["section_intent"] == "New Intent"
        
        # Press 'x' to drop section
        await pilot.press("x")
        assert "summary" in screen._dropped_ids


@pytest.mark.asyncio
async def test_content_review_vim_mode() -> None:
    """Test Vim-mode navigation and annotation in ContentReviewScreen."""
    bus = DemoBus("hitl_3_content_style")
    app = MatchReviewApp(bus=bus, source="demo", job_id="job_123")
    
    async with app.run_test() as pilot:
        await pilot.pause(1.0)
        screen = app.screen
        assert isinstance(screen, ContentReviewScreen)
        editor = screen.query_one("#editor-cv", DocEditor)
        
        # Normal mode: move down
        await pilot.press("j")
        assert editor.cursor_line == 1
        
        # Enter visual mode
        await pilot.press("v")
        assert editor.mode == EditorMode.VISUAL
        assert editor.anchor_line == 1
        
        # Move down in visual mode
        await pilot.press("j")
        assert editor.cursor_line == 2
        
        # Press 'c' to replace
        await pilot.press("c")
        await pilot.pause(0.2)
        assert isinstance(app.screen, AnnotationModal)
        
        # Clear and type replacement
        modal = app.screen
        modal.query_one("#annotation-input").load_text("")
        await pilot.press(*"Replaced Text")
        await pilot.click("#btn-save")
        
        # Verify annotation created
        await pilot.pause(0.2)
        assert isinstance(app.screen, ContentReviewScreen)
        assert editor.mode == EditorMode.NORMAL
        # It should have annotated the segment at line 1 (start of selection)
        seg_id = editor.doc.segment_for_line(1).segment_id
        assert seg_id in editor.annotations
        assert editor.annotations[seg_id].action == "replace"
        assert editor.annotations[seg_id].new_value == "Replaced Text"


@pytest.mark.asyncio
async def test_profile_diff_screen() -> None:
    """Test ProfileDiffScreen display."""
    bus = DemoBus("hitl_4_profile_updates")
    app = MatchReviewApp(bus=bus, source="demo", job_id="job_123")
    
    async with app.run_test() as pilot:
        # Wait more for thread worker and mount
        await pilot.pause(1.5)
        screen = app.screen
        assert isinstance(screen, ProfileDiffScreen)
        
        # Verify surface loaded
        assert screen._surface is not None
        
        # Verify cards are rendered in Static content
        diff_content = screen.query_one("#diff-content", Static)
        assert "skills.languages" in str(diff_content.render())
        
        # Press 'a' to submit
        await pilot.press("a")
        # Screen should be popped after submission
        await pilot.pause(0.5)
        assert not isinstance(app.screen, ProfileDiffScreen)
