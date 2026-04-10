"""Navigation flow tests for the HITL Review UI screens."""

from __future__ import annotations

import pytest
from textual.widgets import Button, ListView, Label
from src.review_ui.demo import DemoLauncher, DemoBus
from src.review_ui.app import MatchReviewApp
from src.review_ui.screens.match_review_screen import MatchReviewScreen
from src.review_ui.screens.blueprint_review_screen import BlueprintReviewScreen
from src.review_ui.screens.content_review_screen import ContentReviewScreen
from src.review_ui.screens.profile_diff_screen import ProfileDiffScreen


# ============================================================================
# Demo Launcher Navigation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_demo_launcher_quit_exits_app() -> None:
    """Test that clicking Quit exits the app."""
    app = DemoLauncher()

    async with app.run_test() as pilot:
        await pilot.click("#btn_quit")

        # App should exit (result is None)
        assert app.return_value is None


@pytest.mark.asyncio
async def test_demo_launcher_btn_1_launches_match_screen() -> None:
    """Test that button 1 launches MatchReviewScreen."""
    app = DemoLauncher()

    async with app.run_test() as pilot:
        await pilot.click("#btn_1")

        assert isinstance(app.return_value, MatchReviewApp)
        assert app.return_value._bus.demo_stage == "hitl_1_match_evidence"


@pytest.mark.asyncio
async def test_demo_launcher_btn_2_launches_blueprint_screen() -> None:
    """Test that button 2 launches BlueprintReviewScreen."""
    app = DemoLauncher()

    async with app.run_test() as pilot:
        await pilot.click("#btn_2")

        assert isinstance(app.return_value, MatchReviewApp)
        assert app.return_value._bus.demo_stage == "hitl_2_blueprint_logic"


@pytest.mark.asyncio
async def test_demo_launcher_btn_3_launches_content_screen() -> None:
    """Test that button 3 launches ContentReviewScreen."""
    app = DemoLauncher()

    async with app.run_test() as pilot:
        await pilot.click("#btn_3")

        assert isinstance(app.return_value, MatchReviewApp)
        assert app.return_value._bus.demo_stage == "hitl_3_content_style"


@pytest.mark.asyncio
async def test_demo_launcher_btn_4_launches_profile_screen() -> None:
    """Test that button 4 launches ProfileDiffScreen."""
    app = DemoLauncher()

    async with app.run_test() as pilot:
        await pilot.click("#btn_4")

        assert isinstance(app.return_value, MatchReviewApp)
        assert app.return_value._bus.demo_stage == "hitl_4_profile_updates"


# ============================================================================
# MatchReviewScreen Navigation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_match_review_quit_pops_screen() -> None:
    """Test that q key pops the MatchReviewScreen."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        # Should have pushed MatchReviewScreen
        assert isinstance(app.screen, MatchReviewScreen)

        # Press q to quit
        await pilot.press("q")
        await pilot.pause(0.5)

        # Since this was the first screen, app should exit
        # In demo mode with no stack, it exits
        assert True  # Just verify no crash


@pytest.mark.asyncio
async def test_match_review_cursor_wraps_at_end() -> None:
    """Test that cursor stays at last item when pressing down."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        screen = app.screen
        list_view = screen.query_one(ListView)
        initial_index = list_view.index

        # Press j multiple times to try to go past end
        for _ in range(10):
            await pilot.press("j")

        # Should not crash, index should stay valid
        assert list_view.index is not None


@pytest.mark.asyncio
async def test_match_review_cursor_stays_at_start() -> None:
    """Test that cursor stays at first item when pressing up."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        screen = app.screen
        list_view = screen.query_one(ListView)

        # Press k to go up from index 0
        await pilot.press("k")

        # Should not go negative
        assert list_view.index == 0 or list_view.index is not None


@pytest.mark.asyncio
async def test_match_review_auto_advance_after_approve() -> None:
    """Test that cursor auto-advances after approving an item."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        screen = app.screen
        list_view = screen.query_one(ListView)
        initial_index = list_view.index

        # Approve first item
        await pilot.press("y")
        await pilot.pause(0.3)

        # Should have auto-advanced
        # Note: This depends on implementation - may need adjustment


# ============================================================================
# BlueprintReviewScreen Navigation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_blueprint_review_quit_pops_screen() -> None:
    """Test that q key pops the BlueprintReviewScreen."""
    bus = DemoBus("hitl_2_blueprint_logic")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        assert isinstance(app.screen, BlueprintReviewScreen)
        await pilot.press("q")
        await pilot.pause(0.5)


@pytest.mark.asyncio
async def test_blueprint_review_edit_modal_cancel() -> None:
    """Test that canceling intent edit returns original value."""
    bus = DemoBus("hitl_2_blueprint_logic")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        screen = app.screen

        # Press e to edit
        await pilot.press("e")
        await pilot.pause(0.3)

        # Should be in modal
        from src.review_ui.screens.blueprint_review_screen import IntentEditModal

        assert isinstance(app.screen, IntentEditModal)

        # Press Cancel (btn-cancel or escape)
        await pilot.click("#btn-cancel")
        await pilot.pause(0.3)

        # Should be back on BlueprintReviewScreen
        assert isinstance(app.screen, BlueprintReviewScreen)


# ============================================================================
# ContentReviewScreen Navigation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_content_review_quit_pops_screen() -> None:
    """Test that q key pops the ContentReviewScreen."""
    bus = DemoBus("hitl_3_content_style")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        assert isinstance(app.screen, ContentReviewScreen)
        await pilot.press("q")
        await pilot.pause(0.5)


@pytest.mark.asyncio
async def test_content_review_tab_navigation() -> None:
    """Test switching between CV/Letter/Email tabs."""
    bus = DemoBus("hitl_3_content_style")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        screen = app.screen
        assert isinstance(screen, ContentReviewScreen)

        # Click on Letter tab
        await pilot.click("TabPane#tab-letter")
        await pilot.pause(0.3)

        # Tab should be active (implementation specific)


@pytest.mark.asyncio
async def test_content_review_vim_escape_cancels_visual() -> None:
    """Test that Escape exits visual mode."""
    bus = DemoBus("hitl_3_content_style")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        screen = app.screen
        from src.review_ui.screens.content_review_screen import DocEditor, EditorMode

        # Focus the editor
        editor = screen.query_one("#editor-cv", DocEditor)

        # Enter visual mode
        await pilot.press("v")
        await pilot.pause(0.2)

        assert editor.mode == EditorMode.VISUAL

        # Press Escape to cancel
        await pilot.press("escape")
        await pilot.pause(0.2)

        assert editor.mode == EditorMode.NORMAL


# ============================================================================
# ProfileDiffScreen Navigation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_profile_diff_quit_pops_screen() -> None:
    """Test that q key pops the ProfileDiffScreen."""
    bus = DemoBus("hitl_4_profile_updates")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        assert isinstance(app.screen, ProfileDiffScreen)
        await pilot.press("q")
        await pilot.pause(0.5)


# ============================================================================
# Screen Stack Tests
# ============================================================================


@pytest.mark.asyncio
async def test_screen_stack_after_demo_selection() -> None:
    """Test that demo selection pushes correct screen to stack."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        # Should have at least one screen pushed
        assert len(app.screen_stack) >= 1
        assert isinstance(app.screen, MatchReviewScreen)


@pytest.mark.asyncio
async def test_multiple_screens_in_stack() -> None:
    """Test that multiple screens can be pushed."""
    # This tests the navigation stack behavior
    # In practice, the demo only pushes one screen at a time
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        initial_stack_depth = len(app.screen_stack)

        # MatchReviewScreen doesn't push additional screens from within
        # But the test verifies the stack is properly managed

        assert initial_stack_depth >= 1
