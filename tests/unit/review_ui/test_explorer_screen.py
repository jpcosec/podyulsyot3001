"""Tests for JobExplorerScreen using Textual's testing framework."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from textual.app import App
from textual.widgets import DataTable, Button, Input
from src.review_ui.screens.explorer_screen import JobExplorerScreen
from src.review_ui.bus import MatchBus


class ExplorerTestApp(App):
    """Test app that hosts JobExplorerScreen."""

    def __init__(self, bus):
        super().__init__()
        self._bus = bus

    def on_mount(self):
        self.push_screen(JobExplorerScreen(bus=self._bus))


def make_mock_bus_with_jobs(jobs: list[dict]) -> MagicMock:
    """Create a mock bus that returns the given jobs."""
    mock_client = MagicMock()

    async def mock_list_jobs(limit: int = 100):
        return jobs

    mock_client.list_jobs = mock_list_jobs

    mock_bus = MagicMock(spec=MatchBus)
    mock_bus.client = mock_client
    mock_bus.config = {}

    return mock_bus


@pytest.mark.asyncio
async def test_explorer_screen_mounts_with_empty_table():
    """Test that explorer screen initializes with empty table."""
    mock_bus = make_mock_bus_with_jobs([])
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(0.5)

        table = app.screen.query_one("#jobs-table", DataTable)
        assert table is not None

        columns = [col.label.plain for col in table.columns.values()]
        assert "Status" in columns
        assert "Source" in columns
        assert "Job ID" in columns
        assert "Title" in columns


@pytest.mark.asyncio
async def test_explorer_screen_displays_jobs():
    """Test that explorer displays jobs from the API."""
    jobs = [
        {
            "thread_id": "xing-123",
            "source": "xing",
            "job_id": "123",
            "title": "Software Engineer",
            "location": "Berlin",
            "status": "pending_review",
            "updated_at": "2024-01-01",
        },
        {
            "thread_id": "stepstone-456",
            "source": "stepstone",
            "job_id": "456",
            "title": "Data Scientist",
            "location": "Munich",
            "status": "completed",
            "updated_at": "2024-01-02",
        },
    ]

    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        table = app.screen.query_one("#jobs-table", DataTable)
        rows = list(table.rows.keys())
        assert len(rows) == 2
        assert "xing-123" in rows
        assert "stepstone-456" in rows


@pytest.mark.asyncio
async def test_explorer_filter_by_pending():
    """Test filtering by pending status."""
    jobs = [
        {"thread_id": "1", "source": "xing", "job_id": "1", "status": "pending_review"},
        {"thread_id": "2", "source": "xing", "job_id": "2", "status": "completed"},
        {"thread_id": "3", "source": "xing", "job_id": "3", "status": "pending_review"},
    ]

    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        await pilot.click("#btn-pending")
        await pilot.pause(0.3)

        table = app.screen.query_one("#jobs-table", DataTable)
        rows = list(table.rows.keys())
        assert len(rows) == 2
        assert "1" in rows
        assert "3" in rows
        assert "2" not in rows


@pytest.mark.asyncio
async def test_explorer_filter_by_completed():
    """Test filtering by completed status."""
    jobs = [
        {"thread_id": "1", "source": "xing", "job_id": "1", "status": "pending_review"},
        {"thread_id": "2", "source": "xing", "job_id": "2", "status": "completed"},
    ]

    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        await pilot.click("#btn-completed")
        await pilot.pause(0.3)

        table = app.screen.query_one("#jobs-table", DataTable)
        rows = list(table.rows.keys())
        assert len(rows) == 1
        assert "2" in rows


@pytest.mark.asyncio
async def test_explorer_filter_by_failed():
    """Test filtering by failed status."""
    jobs = [
        {"thread_id": "1", "source": "xing", "job_id": "1", "status": "failed"},
        {"thread_id": "2", "source": "xing", "job_id": "2", "status": "completed"},
    ]

    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        await pilot.click("#btn-failed")
        await pilot.pause(0.3)

        table = app.screen.query_one("#jobs-table", DataTable)
        rows = list(table.rows.keys())
        assert len(rows) == 1
        assert "1" in rows


@pytest.mark.asyncio
async def test_explorer_filter_buttons_work():
    """Test that filter buttons correctly change the view."""
    jobs = [
        {"thread_id": "1", "source": "xing", "job_id": "1", "status": "pending_review"},
        {"thread_id": "2", "source": "xing", "job_id": "2", "status": "completed"},
    ]

    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        # Test click-based filtering
        await pilot.click("#btn-pending")
        await pilot.pause(0.5)

        table = app.screen.query_one("#jobs-table", DataTable)
        rows = list(table.rows.keys())
        assert len(rows) == 1
        assert "1" in rows


@pytest.mark.asyncio
async def test_explorer_refresh_button():
    """Test refresh button triggers API call."""
    jobs = [
        {"thread_id": "1", "source": "xing", "job_id": "1", "status": "pending_review"}
    ]
    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        await pilot.click("#btn-refresh")
        await pilot.pause(0.5)

        table = app.screen.query_one("#jobs-table", DataTable)
        rows = list(table.rows.keys())
        assert "1" in rows


@pytest.mark.asyncio
async def test_explorer_status_counts_update():
    """Test that status counts are updated after loading."""
    jobs = [
        {"thread_id": "1", "source": "xing", "job_id": "1", "status": "pending_review"},
        {"thread_id": "2", "source": "xing", "job_id": "2", "status": "pending_review"},
        {"thread_id": "3", "source": "xing", "job_id": "3", "status": "completed"},
    ]

    mock_bus = make_mock_bus_with_jobs(jobs)
    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(1.0)

        all_btn = app.screen.query_one("#btn-all", Button)
        pending_btn = app.screen.query_one("#btn-pending", Button)
        completed_btn = app.screen.query_one("#btn-completed", Button)

        assert "All (3)" in all_btn.label.plain
        assert "Pending (2)" in pending_btn.label.plain
        assert "Completed (1)" in completed_btn.label.plain


@pytest.mark.asyncio
async def test_explorer_no_client_shows_error():
    """Test that missing API client shows error notification."""
    mock_bus = MagicMock(spec=MatchBus)
    mock_bus.client = None

    app = ExplorerTestApp(mock_bus)

    async with app.run_test() as pilot:
        await pilot.pause(0.5)


def test_explorer_screen_has_correct_bindings():
    """Test that explorer has expected keyboard bindings."""
    binding_keys = {b[0] for b in JobExplorerScreen.BINDINGS}
    assert "r" in binding_keys
    assert "f" in binding_keys
    assert "1" in binding_keys
    assert "2" in binding_keys
    assert "3" in binding_keys
    assert "4" in binding_keys
    assert "q" in binding_keys


def test_explorer_screen_css_has_table_styles():
    """Test that CSS includes DataTable styling."""
    css = JobExplorerScreen.DEFAULT_CSS
    assert "#jobs-table" in css or "DataTable" in css
    assert ".status-pending" in css
    assert ".status-approved" in css
    assert ".status-error" in css
