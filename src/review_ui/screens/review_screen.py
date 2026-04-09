"""HITL review screen for generate_documents_v2 checkpoints."""

from __future__ import annotations

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    LoadingIndicator,
    RichLog,
    Static,
)

from src.review_ui.bus import MatchBus


class ReviewScreen(Screen):
    """Interactive HITL review screen for one pending checkpoint."""

    BINDINGS = [
        ("a", "approve", "Approve"),
        ("r", "reject", "Reject"),
        ("s", "submit", "Submit review"),
        ("q", "quit_screen", "Quit"),
    ]

    DEFAULT_CSS = """
    ReviewScreen {
        layout: grid;
        grid-size: 1;
    }

    #header-panel {
        height: auto;
        padding: 1 2;
        background: $panel;
        border-bottom: solid $accent;
    }

    #payload-container {
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
    }

    #action-bar {
        height: auto;
        layout: horizontal;
        padding: 1 2;
        background: $panel;
        border-top: solid $accent;
        align: right middle;
    }

    #status-log {
        height: 5;
        border-top: solid $panel;
        background: $surface;
        display: none;
    }

    #status-log.visible {
        display: block;
    }

    #loading {
        display: none;
    }

    #loading.visible {
        display: block;
    }

    #payload {
        text-wrap: wrap;
    }

    .selected {
        border: heavy $accent;
    }
    """

    def __init__(
        self,
        bus: MatchBus,
        source: str,
        job_id: str,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self._source = source
        self._job_id = job_id
        self._surface: Any | None = None
        self._selected_action = "approve"

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        """Compose the review screen layout and action controls."""
        yield Header()
        yield Label("Loading review surface ...", id="header-panel")
        with ScrollableContainer(id="payload-container"):
            yield LoadingIndicator(id="loading", classes="visible")
            yield Static("", id="payload")
        with Horizontal(id="action-bar"):
            yield Button(
                "Approve", id="btn-approve", variant="primary", classes="selected"
            )
            yield Button("Reject", id="btn-reject", variant="error")
            yield Button("Submit review »", id="btn-submit", variant="success")
        yield RichLog(id="status-log", markup=True)
        yield Footer()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        """Start loading the current review surface when the screen mounts."""
        self._load_surface()

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    @work(thread=True, exit_on_error=False)
    def _load_surface(self) -> None:
        """Load the review surface from disk in a background thread."""
        try:
            surface = self._bus.load_current_review_surface(self._source, self._job_id)
            self.app.call_from_thread(self._render_surface, surface)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._show_error, f"{type(exc).__name__}: {exc}")

    @work(thread=True, exit_on_error=False)
    def _submit_review(self, action: str) -> None:
        """Submit the selected review action to LangGraph in a background thread."""
        self.app.call_from_thread(self._disable_submit)
        self.app.call_from_thread(
            self.query_one("#status-log", RichLog).write,
            f"[yellow]Submitting {action} to LangGraph...[/]",
        )
        try:
            result = self._bus.resume_with_review(action)
            status = (
                result.get("status", "unknown") if isinstance(result, dict) else "done"
            )
            self.app.call_from_thread(
                self.query_one("#status-log", RichLog).write,
                f"[green]Graph resumed — final status: [bold]{status}[/bold][/]",
            )
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(
                self.query_one("#status-log", RichLog).write,
                f"[red]Error: {exc}[/]",
            )
            self.app.call_from_thread(self._re_enable_submit)

    # ------------------------------------------------------------------
    # UI updates (called via call_from_thread)
    # ------------------------------------------------------------------

    def _disable_submit(self) -> None:
        """Disable the submit button to prevent double-submit during submission."""
        btn = self.query_one("#btn-submit", Button)
        btn.disabled = True

    def _re_enable_submit(self) -> None:
        """Re-enable the submit button after a failed submission (allows retry)."""
        btn = self.query_one("#btn-submit", Button)
        btn.disabled = False

    def _render_surface(self, surface: Any) -> None:
        """Populate the screen with loaded review surface data."""
        self._surface = surface
        header_panel = self.query_one("#header-panel", Label)
        header_panel.update(
            f"[bold]{surface.title}[/]  ·  {self._source}/{self._job_id}\n"
            f"[dim]Stage: {surface.stage}  ·  Artifact: {surface.artifact_stage}[/]"
        )

        loading = self.query_one("#loading", LoadingIndicator)
        loading.remove_class("visible")
        self.query_one("#payload", Static).update(surface.pretty_json())

    def _show_error(self, message: str) -> None:
        log = self.query_one("#status-log", RichLog)
        log.add_class("visible")
        log.write(f"[red]Error: {message}[/]")

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#btn-approve")
    def _on_approve(self, _: Button.Pressed) -> None:
        self.action_approve()

    @on(Button.Pressed, "#btn-reject")
    def _on_reject(self, _: Button.Pressed) -> None:
        self.action_reject()

    @on(Button.Pressed, "#btn-submit")
    def _on_submit(self, _: Button.Pressed) -> None:
        self.action_submit()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_approve(self) -> None:
        """Select approve as the review action."""
        self._selected_action = "approve"
        self._sync_action_buttons()
        self.notify("Selected action: approve")

    def action_reject(self) -> None:
        """Select reject as the review action."""
        self._selected_action = "reject"
        self._sync_action_buttons()
        self.notify("Selected action: reject")

    def action_submit(self) -> None:
        """Validate and submit the review payload to LangGraph."""
        if self._surface is None:
            self.notify("Review surface not loaded yet.", severity="error")
            return

        log = self.query_one("#status-log", RichLog)
        log.add_class("visible")
        self._submit_review(self._selected_action)

    def action_quit_screen(self) -> None:
        """Pop this screen or quit the app."""
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        else:
            self.app.exit()

    def _sync_action_buttons(self) -> None:
        """Highlight the currently selected action button."""
        approve = self.query_one("#btn-approve", Button)
        reject = self.query_one("#btn-reject", Button)
        if self._selected_action == "approve":
            approve.add_class("selected")
            reject.remove_class("selected")
        else:
            reject.add_class("selected")
            approve.remove_class("selected")
