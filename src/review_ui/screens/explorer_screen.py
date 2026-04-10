"""Job Explorer screen for the Postulator 3000 TUI.

Provides a searchable table of all jobs managed by the LangGraph API,
allowing the user to filter by status and launch reviews.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

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
)

from src.review_ui.bus import MatchBus


class JobExplorerScreen(Screen):
    """Central console for browsing and managing job application threads."""

    BINDINGS = [
        ("r", "refresh", "Refresh list"),
        ("f", "focus_filter", "Focus filter"),
        ("1", "filter_all", "All"),
        ("2", "filter_pending", "Pending"),
        ("3", "filter_completed", "Completed"),
        ("4", "filter_failed", "Failed"),
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

    #status-buttons {
        height: auto;
        padding: 0 2;
        margin-bottom: 1;
        layout: horizontal;
    }

    .filter-btn {
        margin-right: 1;
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
    .status-idle { color: $text-muted; }
    .status-running { color: $primary; }
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
        self._current_filter: str = "all"  # all, pending, completed, failed

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        with Vertical(id="explorer-header"):
            yield Label("[bold]Job Application Dashboard[/bold]", id="title")
            yield Label("Browse and manage LangGraph pipeline threads", id="subtitle")

        with Horizontal(id="filter-container"):
            yield Input(
                placeholder="Search jobs (source, id, city, status)...",
                id="filter-input",
            )
            yield Button("⟳ Refresh", id="btn-refresh", variant="primary")

        with Horizontal(id="status-buttons"):
            yield Button(
                "All (1)", id="btn-all", variant="primary", classes="filter-btn"
            )
            yield Button(
                "Pending (2)", id="btn-pending", variant="default", classes="filter-btn"
            )
            yield Button(
                "Completed (3)",
                id="btn-completed",
                variant="default",
                classes="filter-btn",
            )
            yield Button(
                "Failed (4)", id="btn-failed", variant="default", classes="filter-btn"
            )

        yield DataTable(cursor_type="row", id="jobs-table")

        with Vertical(id="loading-overlay"):
            yield LoadingIndicator(id="loading")

        yield Footer()

    def on_mount(self) -> None:
        """Initial table setup and data fetch."""
        table = self.query_one("#jobs-table", DataTable)
        table.add_columns("Status", "Source", "Job ID", "Title", "Location", "Updated")
        self._update_counts()
        self.action_refresh()

    def _update_counts(self) -> None:
        """Update button labels with counts."""
        all_count = len(self._all_jobs)
        pending_count = sum(
            1 for j in self._all_jobs if j.get("status") == "pending_review"
        )
        completed_count = sum(
            1 for j in self._all_jobs if j.get("status") == "completed"
        )
        failed_count = sum(1 for j in self._all_jobs if j.get("status") == "failed")

        self.query_one("#btn-all", Button).label = f"All ({all_count})"
        self.query_one("#btn-pending", Button).label = f"Pending ({pending_count})"
        self.query_one(
            "#btn-completed", Button
        ).label = f"Completed ({completed_count})"
        self.query_one("#btn-failed", Button).label = f"Failed ({failed_count})"

    def _sync_filter_buttons(self) -> None:
        """Highlight the active filter button."""
        all_btn = self.query_one("#btn-all", Button)
        pending_btn = self.query_one("#btn-pending", Button)
        completed_btn = self.query_one("#btn-completed", Button)
        failed_btn = self.query_one("#btn-failed", Button)

        all_btn.variant = "primary" if self._current_filter == "all" else "default"
        pending_btn.variant = (
            "primary" if self._current_filter == "pending" else "default"
        )
        completed_btn.variant = (
            "primary" if self._current_filter == "completed" else "default"
        )
        failed_btn.variant = (
            "primary" if self._current_filter == "failed" else "default"
        )

    @work(thread=True)
    def action_refresh(self) -> None:
        """Fetch latest job list from LangGraph API.

        Runs in a background worker to keep the TUI responsive.
        """
        self.app.call_from_thread(setattr, self.query_one("#loading"), "display", True)
        self.app.call_from_thread(setattr, self.query_one("#jobs-table"), "display", False)

        if not self._bus.client:
            self.app.call_from_thread(
                self.notify,
                "No API client configured. Run with LangGraph API active.",
                severity="error",
            )
            return

        try:
            # list_jobs is async, so we need a loop since we are in a thread worker
            loop = asyncio.new_event_loop()
            try:
                jobs_data = loop.run_until_complete(self._bus.client.list_jobs(limit=100))
            finally:
                loop.close()

            self._all_jobs = jobs_data
            self.app.call_from_thread(self._update_counts)
            self.app.call_from_thread(self._apply_filter)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Failed to refresh jobs: {e}", severity="error")
        finally:
            self.app.call_from_thread(setattr, self.query_one("#loading"), "display", False)
            self.app.call_from_thread(setattr, self.query_one("#jobs-table"), "display", True)

    def _apply_filter(self) -> None:
        """Apply the current filter to the table."""
        search = self.query_one("#filter-input", Input).value
        self._update_table(self._all_jobs, search, self._current_filter)

    def _update_table(
        self,
        jobs: List[Dict[str, Any]],
        filter_text: str = "",
        status_filter: str = "all",
    ) -> None:
        """Update the DataTable with filtered job results.

        Args:
            jobs: List of job state dictionaries.
            filter_text: Optional string to filter the list.
            status_filter: Status filter (all, pending, completed, failed).
        """
        table = self.query_one("#jobs-table", DataTable)
        table.clear()

        filter_text = filter_text.lower()

        for job in jobs:
            status = job.get("status", "unknown")

            # Apply status filter
            if status_filter == "pending" and status != "pending_review":
                continue
            if status_filter == "completed" and status != "completed":
                continue
            if status_filter == "failed" and status != "failed":
                continue

            # Apply search filter
            search_str = f"{job.get('source')} {job.get('job_id')} {job.get('location')} {job.get('title', '')} {status}".lower()
            if filter_text and filter_text not in search_str:
                continue

            status_display, status_style = self._format_status(status)

            table.add_row(
                status_display,
                job.get("source", "N/A"),
                job.get("job_id", "N/A"),
                job.get("title", "N/A")[:30],
                job.get("location", "N/A"),
                job.get("updated_at", "N/A"),
                key=job["thread_id"],
                label=status_style,
            )

    def _format_status(self, status: str) -> tuple[str, str]:
        """Format status for display with styling."""
        if status == "pending_review":
            return "⏳ PENDING", "status-pending"
        elif status == "completed":
            return "✅ COMPLETE", "status-approved"
        elif status == "failed":
            return "❌ FAILED", "status-error"
        elif status == "idle":
            return "○ IDLE", "status-idle"
        elif status == "running":
            return "▶ RUNNING", "status-running"
        else:
            return f" {status.upper()}", "status-idle"

    @on(Input.Changed, "#filter-input")
    def _on_filter_changed(self, event: Input.Changed) -> None:
        self._apply_filter()

    @on(Button.Pressed, "#btn-refresh")
    def _on_refresh_pressed(self) -> None:
        self.action_refresh()

    @on(Button.Pressed, "#btn-all")
    def _on_all_pressed(self) -> None:
        self._current_filter = "all"
        self._sync_filter_buttons()
        self._apply_filter()

    @on(Button.Pressed, "#btn-pending")
    def _on_pending_pressed(self) -> None:
        self._current_filter = "pending"
        self._sync_filter_buttons()
        self._apply_filter()

    @on(Button.Pressed, "#btn-completed")
    def _on_completed_pressed(self) -> None:
        self._current_filter = "completed"
        self._sync_filter_buttons()
        self._apply_filter()

    @on(Button.Pressed, "#btn-failed")
    def _on_failed_pressed(self) -> None:
        self._current_filter = "failed"
        self._sync_filter_buttons()
        self._apply_filter()

    @on(DataTable.RowSelected)
    def _on_row_selected(self, event: DataTable.RowSelected) -> None:
        thread_id = event.row_key.value
        job = next((j for j in self._all_jobs if j["thread_id"] == thread_id), None)
        if not job:
            return

        if job.get("has_review_pending"):
            self.notify(f"Launching review for {job['source']}/{job['job_id']}...")
            self._bus.config = {"configurable": {"thread_id": thread_id}}
            # Use the app's routing logic
            self.app._push_stage_screen(job["source"], job["job_id"])
        else:
            self.notify(
                f"Job {job['job_id']} is {job['status']}. No review needed.",
                severity="information",
            )

    def action_focus_filter(self) -> None:
        """Focus the filter input widget for keyboard-driven searching."""
        self.query_one("#filter-input").focus()

    def action_filter_all(self) -> None:
        self._current_filter = "all"
        self._sync_filter_buttons()
        self._apply_filter()

    def action_filter_pending(self) -> None:
        self._current_filter = "pending"
        self._sync_filter_buttons()
        self._apply_filter()

    def action_filter_completed(self) -> None:
        self._current_filter = "completed"
        self._sync_filter_buttons()
        self._apply_filter()

    def action_filter_failed(self) -> None:
        self._current_filter = "failed"
        self._sync_filter_buttons()
        self._apply_filter()
