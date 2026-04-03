"""Job Explorer screen for the Postulator 3000 TUI.

Provides a searchable table of all jobs managed by the LangGraph API,
allowing the user to filter by status and launch reviews.
"""

from __future__ import annotations

import asyncio
from typing import Any, List

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Static,
)

from src.review_ui.bus import MatchBus
from src.review_ui.screens.review_screen import ReviewScreen


class JobExplorerScreen(Screen):
    """Central console for browsing and managing job application threads."""

    BINDINGS = [
        ("r", "refresh", "Refresh list"),
        ("f", "focus_filter", "Focus filter"),
        ("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    JobExplorerScreen {
        background: $surface;
    }

    #explorer-header {
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $accent;
    }

    #filter-container {
        height: auto;
        padding: 0 2;
        margin-bottom: 1;
    }

    DataTable {
        height: 1fr;
        margin: 1 2;
        border: tall $panel;
    }

    #loading-overlay {
        align: center middle;
        height: 1fr;
    }

    .status-pending { color: $warning; text-style: bold; }
    .status-approved { color: $success; text-style: bold; }
    .status-rejected { color: $error; text-style: bold; }
    .status-error { color: $error; text-style: italic; }
    """

    def __init__(self, bus: MatchBus, **kwargs: Any) -> None:
        """Initialize the explorer screen.

        Args:
            bus: The communication bus for backend interaction.
            **kwargs: Additional Textual screen arguments.
        """
        super().__init__(**kwargs)
        self._bus = bus
        self._all_jobs: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        with Vertical(id="explorer-header"):
            yield Label("[bold]Job Application Manager[/bold]", id="title")
            yield Label("Browse and manage LangGraph pipeline threads", id="subtitle")

        with Horizontal(id="filter-container"):
            yield Input(
                placeholder="Filter jobs (source, id, city, status)...",
                id="filter-input",
            )
            yield Button("Refresh", id="btn-refresh", variant="primary")

        yield DataTable(cursor_type="row", id="jobs-table")

        with Vertical(id="loading-overlay"):
            yield LoadingIndicator(id="loading")

        yield Footer()

    def on_mount(self) -> None:
        """Initial table setup and data fetch."""
        table = self.query_one("#jobs-table", DataTable)
        table.add_columns("Status", "Source", "Job ID", "City", "Updated")
        self.action_refresh()

    @work(thread=True)
    async def action_refresh(self) -> None:
        """Fetch latest job list from LangGraph API.

        Runs in a background worker to keep the TUI responsive.
        """
        self.query_one("#loading").display = True
        self.query_one("#jobs-table").display = False

        if not self._bus.client:
            self.notify(
                "No API client configured. Run with LangGraph API active.",
                severity="error",
            )
            return

        try:
            # list_jobs already returns enriched states in the refactored client
            jobs_data = await self._bus.client.list_jobs(limit=100)
            self._all_jobs = jobs_data
            self.app.call_from_thread(self._update_table, jobs_data)
        except Exception as e:
            self.notify(f"Failed to refresh jobs: {e}", severity="error")
        finally:
            self.query_one("#loading").display = False
            self.query_one("#jobs-table").display = True

    def _update_table(self, jobs: List[Dict[str, Any]], filter_text: str = "") -> None:
        """Update the DataTable with filtered job results.

        Args:
            jobs: List of job state dictionaries.
            filter_text: Optional string to filter the list.
        """
        table = self.query_one("#jobs-table", DataTable)
        table.clear()

        filter_text = filter_text.lower()

        for job in jobs:
            # Simple matching for filter across all visible fields
            search_str = f"{job.get('source')} {job.get('job_id')} {job.get('location')} {job.get('status')}".lower()
            if filter_text and filter_text not in search_str:
                continue

            status = job.get("status", "unknown")
            status_style = ""

            # Semantic status mapping
            if status == "pending_review":
                status_display = "⏳ PENDING"
                status_style = "status-pending"
            elif status == "completed":
                status_display = "✅ APPROVED"
                status_style = "status-approved"
            elif status == "failed":
                status_display = "❌ ERROR"
                status_style = "status-error"
            else:
                status_display = f" {status.upper()}"

            table.add_row(
                status_display,
                job.get("source", "N/A"),
                job.get("job_id", "N/A"),
                job.get("location", "N/A"),
                job.get("updated_at", "N/A"),
                key=job["thread_id"],
                label=status_style,
            )

    @on(Input.Changed, "#filter-input")
    def _on_filter_changed(self, event: Input.Changed) -> None:
        self._update_table(self._all_jobs, event.value)

    @on(Button.Pressed, "#btn-refresh")
    def _on_refresh_pressed(self) -> None:
        self.action_refresh()

    @on(DataTable.RowSelected)
    def _on_row_selected(self, event: DataTable.RowSelected) -> None:
        thread_id = event.row_key.value
        # Find job metadata
        job = next((j for j in self._all_jobs if j["thread_id"] == thread_id), None)
        if not job:
            return

        if job.get("has_review_pending"):
            self.notify(f"Launching review for {job['source']}/{job['job_id']}...")
            # Push ReviewScreen
            # We need to update the bus config with the correct thread_id
            self._bus.config = {"configurable": {"thread_id": thread_id}}
            self.app.push_screen(
                ReviewScreen(bus=self._bus, source=job["source"], job_id=job["job_id"])
            )
        else:
            self.notify(
                f"Job {job['job_id']} is {job['status']}. No review needed.",
                severity="information",
            )

    def action_focus_filter(self) -> None:
        """Focus the filter input widget for keyboard-driven searching."""
        self.query_one("#filter-input").focus()
