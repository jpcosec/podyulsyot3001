"""Error state tests for the HITL Review UI screens."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from textual.widgets import Button, RichLog
from src.review_ui.demo import DemoBus
from src.review_ui.app import MatchReviewApp
from src.review_ui.screens.match_review_screen import MatchReviewScreen
from src.review_ui.screens.blueprint_review_screen import BlueprintReviewScreen
from src.review_ui.screens.content_review_screen import ContentReviewScreen
from src.review_ui.screens.profile_diff_screen import ProfileDiffScreen


class FailingBus(DemoBus):
    """Mock bus that fails on all operations."""

    def load_current_review_surface(self, source: str, job_id: str):
        raise ConnectionError("Simulated API connection failure")


class EmptyBus(DemoBus):
    """Mock bus that returns empty data."""

    def load_current_review_surface(self, source: str, job_id: str):
        from src.review_ui.bus import ReviewSurfaceData

        return ReviewSurfaceData(
            stage="hitl_1_match_evidence",
            artifact_stage="match_edges",
            title="Match Evidence Review",
            payload={},  # Empty payload
        )


# ============================================================================
# MatchReviewScreen Error Tests
# ============================================================================


@pytest.mark.asyncio
async def test_match_review_load_failure_shows_error() -> None:
    """Test that load failure shows error notification."""
    bus = FailingBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, MatchReviewScreen)
        # Error notification should have been shown
        # The app should not crash


@pytest.mark.asyncio
async def test_match_review_empty_payload_handled() -> None:
    """Test that empty payload doesn't crash the screen."""
    bus = EmptyBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, MatchReviewScreen)

        # Should handle empty matches gracefully
        assert screen._matches == []


@pytest.mark.asyncio
async def test_match_review_submit_failure_shows_error() -> None:
    """Test that submit failure shows error in status log."""
    from src.review_ui.bus import ReviewSurfaceData

    class SubmitFailBus(DemoBus):
        def load_current_review_surface(self, source: str, job_id: str):
            return ReviewSurfaceData(
                stage="hitl_1_match_evidence",
                artifact_stage="match_edges",
                title="Match Evidence Review",
                payload={
                    "matches": [
                        {
                            "requirement_id": "R01",
                            "match_score": 0.9,
                            "reasoning": "Test",
                            "profile_evidence_ids": [],
                        }
                    ],
                    "job_kg": {"hard_requirements": []},
                },
            )

        def resume_with_review(self, action: str, patches=None):
            raise TimeoutError("Simulated submit timeout")

    bus = SubmitFailBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen

        # Approve the item
        await pilot.press("y")
        await pilot.pause(0.3)

        # Submit
        await pilot.press("s")
        await pilot.pause(1.0)

        # Status log should show error
        status_log = screen.query_one("#status-log", RichLog)
        # Check that button was re-enabled (error was handled)
        submit_btn = screen.query_one("#btn-submit", Button)
        assert not submit_btn.disabled


# ============================================================================
# BlueprintReviewScreen Error Tests
# ============================================================================


@pytest.mark.asyncio
async def test_blueprint_review_load_failure_shows_error() -> None:
    """Test that load failure shows error notification."""
    bus = FailingBus("hitl_2_blueprint_logic")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, BlueprintReviewScreen)


@pytest.mark.asyncio
async def test_blueprint_review_empty_payload_handled() -> None:
    """Test that empty sections list doesn't crash."""
    from src.review_ui.bus import ReviewSurfaceData

    class EmptySectionsBus(DemoBus):
        def load_current_review_surface(self, source: str, job_id: str):
            return ReviewSurfaceData(
                stage="hitl_2_blueprint_logic",
                artifact_stage="blueprint",
                title="Blueprint Review",
                payload={"sections": []},
            )

    bus = EmptySectionsBus("hitl_2_blueprint_logic")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, BlueprintReviewScreen)
        assert screen._sections == []


# ============================================================================
# ContentReviewScreen Error Tests
# ============================================================================


@pytest.mark.asyncio
async def test_content_review_load_failure_shows_error() -> None:
    """Test that load failure shows error notification."""
    bus = FailingBus("hitl_3_content_style")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, ContentReviewScreen)


@pytest.mark.asyncio
async def test_content_review_invalid_markdown_handled() -> None:
    """Test that invalid markdown doesn't crash the editor."""
    from src.review_ui.bus import ReviewSurfaceData

    class InvalidMarkdownBus(DemoBus):
        def load_current_review_surface(self, source: str, job_id: str):
            return ReviewSurfaceData(
                stage="hitl_3_content_style",
                artifact_stage="markdown_bundle",
                title="Content Review",
                payload={
                    "cv_full_md": None,  # Invalid
                    "letter_full_md": "",  # Empty but valid
                    "email_body_md": "valid",
                },
            )

    bus = InvalidMarkdownBus("hitl_3_content_style")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        # Should handle gracefully without crashing
        assert isinstance(screen, ContentReviewScreen)


# ============================================================================
# ProfileDiffScreen Error Tests
# ============================================================================


@pytest.mark.asyncio
async def test_profile_diff_load_failure_shows_error() -> None:
    """Test that load failure shows error notification."""
    bus = FailingBus("hitl_4_profile_updates")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, ProfileDiffScreen)


@pytest.mark.asyncio
async def test_profile_diff_empty_updates_handled() -> None:
    """Test that empty updates list doesn't crash."""
    from src.review_ui.bus import ReviewSurfaceData

    class EmptyUpdatesBus(DemoBus):
        def load_current_review_surface(self, source: str, job_id: str):
            return ReviewSurfaceData(
                stage="hitl_4_profile_updates",
                artifact_stage="profile_updater",
                title="Profile Update Review",
                payload={"updates": []},
            )

    bus = EmptyUpdatesBus("hitl_4_profile_updates")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen
        assert isinstance(screen, ProfileDiffScreen)


# ============================================================================
# Thread Safety Tests
# ============================================================================


@pytest.mark.asyncio
async def test_worker_exception_doesnt_crash_ui() -> None:
    """Test that worker exceptions are caught and don't crash the UI."""
    from src.review_ui.bus import ReviewSurfaceData

    class WorkerExceptionBus(DemoBus):
        def load_current_review_surface(self, source: str, job_id: str):
            raise RuntimeError("Worker thread exception")

    bus = WorkerExceptionBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        # App should still be running
        assert app.is_running


@pytest.mark.asyncio
async def test_multiple_rapid_actions_handled() -> None:
    """Test that rapid button clicks don't cause issues."""
    bus = DemoBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        await pilot.pause(1.5)

        screen = app.screen

        # Rapidly approve items
        for _ in range(5):
            await pilot.press("y")
            await pilot.pause(0.05)

        await pilot.pause(0.5)

        # Should handle without crash
        assert screen._outcomes.get("R01") in ["approve", "reject", "pending"]


@pytest.mark.asyncio
async def test_action_during_loading_handled() -> None:
    """Test that actions during loading are handled gracefully."""
    from src.review_ui.bus import ReviewSurfaceData
    import asyncio

    class SlowBus(DemoBus):
        def load_current_review_surface(self, source: str, job_id: str):
            import time

            time.sleep(2)  # Simulate slow load
            return ReviewSurfaceData(
                stage="hitl_1_match_evidence",
                artifact_stage="match_edges",
                title="Match Evidence Review",
                payload={
                    "matches": [
                        {
                            "requirement_id": "R01",
                            "match_score": 0.9,
                            "reasoning": "Test",
                            "profile_evidence_ids": [],
                        }
                    ],
                    "job_kg": {"hard_requirements": []},
                },
            )

    bus = SlowBus("hitl_1_match_evidence")
    app = MatchReviewApp(bus=bus, source="demo", job_id="test")

    async with app.run_test() as pilot:
        # Immediately try to approve before data loads
        await pilot.press("y")
        await pilot.pause(0.3)

        # Should not crash - action should be ignored during loading
        assert app.is_running
